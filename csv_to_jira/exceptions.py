class CsvToJiraError(Exception):
    pass


class UserError(CsvToJiraError):
    pass


class ConfigurationError(UserError):
    pass


class Abort(CsvToJiraError):
    pass
