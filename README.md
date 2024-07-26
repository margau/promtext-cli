# promtext-cli

promtext-cli is a tool for creating prometheus text files from a simple cli command.

It is intended for use with cronjob scripts (e.g. backups).

Features:
- supports merging new metrics into existing files
- metrics will be updated (same labelset or no labels given), or appended to existing metrics as new timeseries
- currently only supports gauge metrics

## Usage
```
promtext -h
usage: main.py [-h] [--docs DOCS] [--label KEY=VALUE] [-v] filename metric value

Prometheus textfile helper

positional arguments:
  filename           Path to existing or new prometheus textfile, will be updated
  metric             metric name (new or updated)
  value              metric value

options:
  -h, --help         show this help message and exit
  --docs DOCS        metric documentation
  --label KEY=VALUE  label key=value pairs
  -v, --verbose
```

## Examples
`tmp/backup.prom` before:
```
# HELP backup_last_start 
# TYPE backup_last_start gauge
backup_last_start{backup="example_1"} 1.721923501e+09
# HELP backup_last_end 
# TYPE backup_last_end gauge
backup_last_end{backup="example_1"} 1.721989156e+09
# HELP backup_last_exit 
# TYPE backup_last_exit gauge
backup_last_exit{backup="example_1"} 2.0
```

Updating existing timeseries: `promtext tmp/backup.prom backup_last_start 0 --label backup=example_1`:
```
# HELP backup_last_start 
# TYPE backup_last_start gauge
backup_last_start{backup="example_1"} 0.0
# HELP backup_last_end 
# TYPE backup_last_end gauge
backup_last_end{backup="example_1"} 1.721989156e+09
# HELP backup_last_exit 
# TYPE backup_last_exit gauge
backup_last_exit{backup="example_1"} 2.0
```

Adding a new label: `promtext tmp/backup.prom backup_last_start 0 --label backup=example_2`
```
# HELP backup_last_start 
# TYPE backup_last_start gauge
backup_last_start{backup="example_1"} 0.0
backup_last_start{backup="example_2"} 0.0
# HELP backup_last_end 
# TYPE backup_last_end gauge
backup_last_end{backup="example_1"} 1.721989156e+09
# HELP backup_last_exit 
# TYPE backup_last_exit gauge
backup_last_exit{backup="example_1"} 2.0
```

Adding a new metric: `promtext tmp/backup.prom some_other_state 0 --label new_label=foo_bar`
```
# HELP backup_last_start 
# TYPE backup_last_start gauge
backup_last_start{backup="example_1"} 0.0
backup_last_start{backup="example_2"} 0.0
# HELP backup_last_end 
# TYPE backup_last_end gauge
backup_last_end{backup="example_1"} 1.721989156e+09
# HELP backup_last_exit 
# TYPE backup_last_exit gauge
backup_last_exit{backup="example_1"} 2.0
# HELP some_other_state metric appended by promtext-cli
# TYPE some_other_state gauge
some_other_state{new_label="foo_bar"} 0.0
```

However, changing the label keys does not work:
```
promtext tmp/backup.prom some_other_state 0 --label foo_bar=foo_bar  
ERROR:promtext_cli.main:labelnames for metric some_other_state not compatible, cannot update! Old: ['new_label'], New: ['foo_bar']
```
