# Changelog

2021/06/22

- The environment is passed into the `LocalRunner`, which is also forwarded by
  `sudo` through passing the `-E` flag.
- Generic files and/or directories place inside a trial directory are ignored
  and not attempted to be processed as patients in `trial run` and similar
  commands.

2021/06/30

- Add support for [`QCG-PilotJob`](https://github.com/vecma-project/QCG-PilotJob)
  as a runner for the trials.
- Add the `--qcg` flag to invoke the `QCGRunner` to run trials.

2021/07/02

- Change default archive filename `trial_data.RData` to
  `trial_outome_data.RData`.

2021/07/12

- Event pipelines are propagated from the criteria files (`criteria.yml`) into
  the patient configuration files (`trial/patient_*/patient.yml`) such that
  different pipelines can be defined directly in the criteria files.
- Providing `--clean-files` does not accidentally clean up the files in
  combination with the `-x` (dry-run) flag.

2021/07/26

- Change `--keep-files/--clean-files` toggles to `--clean-files OPTION` where
  three choices are possible: `none`, `1mb`, or `all`. The first two, `none` and
  `1mb` mimic the original behaviour with `--keep-files/--clean-files`
  respectively. The new `all` flag performs more aggressive file cleaning and
  removes any file---except for YAML files with `.yml` or `.yaml`
  suffix---regardless of the required disk space.
- Add a [`CleanFiles`](desist/isct/utilities.py) enumerated type to keep track
  of file cleaning modes.
- Add a [`FileCleaner`](desist/isct/utilities.py) utility class that handles
  file cleaning and supersedes the separate `clean_large_files` utility
  function.
- Add `Runner.wait()` function to avoid type assertion in `QCGRunner.run()`.
