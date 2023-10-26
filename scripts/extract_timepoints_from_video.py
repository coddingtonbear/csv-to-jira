"""Create segments using information from the chat log for a meeting recording

Using this:

- During your meeting:
  - You record your meeting.
  - During the meeting *after* you've completed ticketing something,
    you say in the chat "Ticketed: <TOPIC>"
- After your meeting:
  - Download your meeting recording and chat log (*not* transcript).
  - You run this script passing the necessary command-line args.
  - You upload your videos somewhere and attach them to tickets!

Theory of Operation:

1. Identify segments of time by reading the chat log. The chat log is composed of sections like::

  00:51:07.126,00:51:10.126
  Adam Coddington: Ticketed: Expiry
  
  00:54:20.880,00:54:23.880
  Adam Coddington: Ticketed: Copy

Each chat message has two comma-separated timestamps: one for, I think,
the moment the user started typing the message, and one for, I think,
the moment the user sent it.  We'll only use the first of them.

From these, we can infer when we've stopped talking about some topic;
so the segment to create spans from the immediately-preceding "Ticketed:"
entry to the "Ticketed:" entry.  For example, the segment about "Copy"
ranges from 00:51:07 to 00:54:20.

2. For each segment, generate a video that includes only that time range.

"""

from argparse import ArgumentParser, FileType
from pathlib import Path
import dataclasses
import datetime
import re
import subprocess
import sys
from typing import Iterable, IO


TIMEPOINT_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})"
    r",(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})$"
)
SECTION_RE = re.compile(
    r"^[^:]*: Ticketed:(?P<name>.*)$"
)


class SnippetFailed(Exception):
    pass


@dataclasses.dataclass
class VideoSegment:
    name: str
    start: datetime.timedelta
    end: datetime.timedelta


def get_segments(start_seconds: int, file: IO[str]) -> Iterable[VideoSegment]:
    cursor_start = datetime.timedelta(seconds=start_seconds)
    cursor_end = datetime.timedelta(0)

    for line in file:
        if timepoint := TIMEPOINT_RE.match(line):
            hours, minutes, seconds = timepoint.groupdict()['start'].split(':')
            cursor_end = datetime.timedelta(
                hours=int(hours),
                minutes=int(minutes),
                seconds=float(seconds),
            )

        if section := SECTION_RE.match(line):
            yield VideoSegment(
                section.groupdict()['name'].strip(),
                start=cursor_start,
                end=cursor_end
            )
            cursor_start = cursor_end


def generate_snippet(
    file_path: Path,
    segment: VideoSegment
) -> Path:
    segment_name = segment.name.replace('/', ' ')
    filename = Path(
        f"{file_path.parent}/{file_path.stem} - {segment_name}{file_path.suffix}"
    )
    proc = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(segment.start),
            "-to",
            str(segment.end),
            "-i",
            file_path,
            "-c",
            "copy",
            filename,
        ]
    )
    result = proc.wait()
    if result != 0:
        raise SnippetFailed()

    return filename


def main(sys_args):
    parser = ArgumentParser()
    parser.add_argument(
        '--start-seconds',
        '-s',
        type=int,
        help=(
            "Number of seconds after the beginning of the recording "
            "to not include in a snippet"
        ),
        default=0
    )
    parser.add_argument('input_video', type=Path)
    parser.add_argument('chat_log', type=FileType('r'))
    args = parser.parse_args(sys_args)

    for segment in get_segments(args.start_seconds, args.chat_log):
        filename = generate_snippet(args.input_video, segment)
        print(filename)


if __name__ == '__main__':
    main(sys.argv[1:])
