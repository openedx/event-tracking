# Change Log

## Kinesis backend:

Added kinesis backend which sends all the event data to kinesis directly. In this kinesis backend we are using `boto`. In order to send the event directly to kinesis from the application we need to follow the configurations in aws.

1.) `boto` should have the role defined to list, read, write into kinesis.

2.) Specifically, boto should have access to `put_record` or `put_records` method to send the event data.
