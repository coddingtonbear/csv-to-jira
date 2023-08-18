# Csv-to-Jira

I very often need to programmatically create issues and their dependencies;
this is a tool I've written for managing issues in Jira via a CSV file describing those issues.

# Quickstart

Create a CSV file having the following columns:

- `ID`: (Required) A human-defined ID for this record.  This is used for helping you indicate dependencies for entries not yet having ticket numbers in Jira.
- `Summary`: (Required) A summary for your issue.
- `Size`: A sizing, in story points, for your issue.
- Description-related fields; these will be joined into a single description field in Jira:
  - `Description`: A description for your issue.
  - `Details`: Some details about your issue.
  - `Story`: A user story for your issue.
  - `Notes`: Some notes for your issue.
- `Labels`: A space-separated list of labels to add to your issue.  Will be combined with `--label` options provided at the command-line.
- `Issuetype`: The name of the type of issue to create.  If undefined, will fallback to use `--issuetype` command-line argument.
- `Depends`: A comma-separated list of dependencies for this issue.  This can be either an ID as specified in another row's `id` field or a Jira ticket number.

Run the following command, replacing MYPROJECT with the short name of the Jira project you would like these issues created within:

```bash
csv-to-jira create-issues /path/to/csv/file.csv MYPROJECT
```

Your issues will be created, and the file you referenced will be updated to include a column indicating the ticket numbers for the issues created.

See `create-issues` below for more options.

## Commands

### digraph

Create a digraph showing your CSV & its inter-issue dependencies.


### create-issues

Create any issues (or relationships) described in your CSV that do not
currently exist in Jira.

Extra options:

- `--setfield`: Set a particular issue field to a particular value.  E.g.: `--setfield="myfield=myvalue"`.  Can be specified multiple times to set multiple fields' values.
- `--label`: Add a label to created issues.  E.g.: `--label=frontend`. Can be specified multiple times to add multiple labels.
- `--issuetype`: Select an issue type for your issue.  By default: `Story`.
- `--relationship`: Select the type of relationship used for indicating dependencies.  By default: `Blocks`.
