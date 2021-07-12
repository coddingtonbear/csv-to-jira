# Csv-to-Jira

I very often need to programmatically create issues and their dependencies;
this is a tool I've written for managing issues in Jira via a CSV file describing those issues.


## Commands

### digraph

Create a digraph showing your CSV & its inter-issue dependencies.


### create-issues

Create any issues (or relationships) described in your CSV that do not
currently exist in Jira.
