import pathlib
import os
import pandas as pd
import subprocess
import shutil

from easyvvuq.encoders import BaseEncoder
from easyvvuq.decoders import BaseDecoder
from easyvvuq import OutputType
from workflow.patient import Patient


class ISCTEncoder(BaseEncoder, encoder_name="ISCTEncoder"):
    def __init__(self, template_fname, target_filename=None):
        # template patient directory, e.g. `/path/patient_000`
        if isinstance(template_fname, pathlib.PosixPath):
            template_fname = str(template_fname)

        self.template_fname = template_fname

        # target patient directory, `patient_000` in `/run_000/`
        self.target_filename = os.path.basename(self.template_fname)

    def encode(self, params={}, target_dir=''):
        """Encode the parameter files into a copy of the patient YAML."""

        # copy original patient directory and all its contents
        orig = pathlib.Path(self.template_fname).absolute()
        copy = pathlib.Path(target_dir).absolute()

        # TODO: replace directory copy by default functionality of EasyVVUQ by
        # wrapping our ISCTEncoder together with a directory encoder.

        # add "/." to copy contents including hidden directories
        subprocess.run(["cp", "-r", f"{str(orig)}/.", copy])

        # files to be reset/removed
        remove = ['clot_present', 'thrombectomy_outcome.txt']

        # directories to remove them from
        dirs = [copy]
        for p in ['baseline', 'stroke', 'treatment']:
            dirs.append(copy.joinpath(p))

        # travers directories and remove desired files
        for d in dirs:
            for f in filter(os.path.isfile, d.iterdir()):
                f = pathlib.Path(f)
                if f.name in remove:
                    os.remove(f)

        # load the template patient configuration
        patient = Patient.from_yaml(self.template_fname)

        # change its filename
        patient.dir = pathlib.Path(target_dir).absolute()

        # update parameters: this updates all parameters that are read from
        # either the `patient.yml` or the `congfig.xml`.

        # attempt: update only parameters that are already present, if not,
        # we either are inserting them, which might or might not be what we
        # want to do, or we should update them otherwise
        for k, v in params.items():
            if k in patient:
                patient[k] = v

        done = [k for k, _ in params.items() if k in patient]
        for k in done:
            del params[k]


        # all parameters located in `bf_sim/Model_parameters.txt`
        options = ["BLOOD_VISC", "StrokeVolume", "Density", "SystolePressure",
                 "DiastolePressure",]
        matches = [(k,v) for k, v in params.items() if k in options]

        # update the matches only
        for k, v in matches:

            # update the patient config with these parameters
            patient[k] = v

            # read in template parameters
            with open(copy.joinpath("tmp.txt"), "w") as outfile:
                with open(orig.joinpath("bf_sim/Model_parameters.txt"),
                          "r") as config:
                    for line in config:
                        key = line.strip().split("=")[0]
                        if key == k:
                            outfile.write(f"{key}={patient[key]}\n")
                        else:
                            outfile.write(line)

            shutil.move(copy.joinpath("tmp.txt"), orig.joinpath("bf_sim/Model_parameters.txt"))
            del params[k]

        # assert the `params` dictionary is empty, indicating that all the
        # parameters have been encoded towards a location
        assert params == {}

        # dump patient to yaml and xml
        patient.to_yaml()
        patient.to_xml()

    def _log_substitution_failure(self, exception):
        # TODO
        pass

    def get_restart_dict(self):
        # TODO: temporary to fill requirement of returning some dict
        return {
            "target_filename": self.target_filename,
            "template_fname": self.template_fname
        }

    def element_version(self):
        # TODO: temporary to fill required function
        return "0.1"


class ISCTDecoder(BaseDecoder, decoder_name="ISCTDecoder"):
    def __init__(self, target_filename=None, output_columns=None):
        self.target_filename = target_filename
        self.output_columns = output_columns
        self.output_type = OutputType('sample')

    def sim_complete(self, run_info=None):
        """Return True if the simulation was completed."""
        # TODO: without run info we cannot extract anything?
        assert run_info is not None

        run_path = pathlib.Path(run_info['run_dir'])
        assert os.path.isdir(run_path)

        # TODO: so far this just checks if the `patient.yml` is there... So we
        # might want to consider printing another file to indicate it is done,
        # or to simply traverse the patient config and check all events are
        # set to done.
        return os.path.isfile(run_path.joinpath(self.target_filename))

    def parse_sim_output(self, run_info={}):
        # TODO: without run info we cannot extract anything?
        assert run_info is not None

        run_path = pathlib.Path(run_info['run_dir'])
        assert os.path.isdir(run_path)

        # patient = Patient.from_yaml(run_path.joinpath(self.target_filename))

        patient = Patient.from_yaml(run_path.joinpath("patient.yml"))

        data = []

        # for col in self.output_columns:
        #     if isinstance(col, str):
        #         data.append([(col, 0), [1])
        # data = [(("age"), 50), (("HeartRate"), 100)]

        if "pressure_drop" in self.output_columns:
            with open(run_path.joinpath(self.target_filename), "r") as f:
                dP = float(f.read().splitlines()[-1].split(",")[-1])

            data = [(("pressure_drop", 0), [dP]),
                    (("BLOOD_VISC", 0), [patient["BLOOD_VISC"]])]

        return pd.DataFrame(dict(data))

    def _log_substitution_failure(self, exception):
        # TODO
        pass

    def get_restart_dict(self):
        # TODO: temporary to fill requirement of returning some dict
        return {
            "target_filename": self.target_filename,
            "output_columns": self.output_columns
        }

    def element_version(self):
        # TODO: temporary to fill required function
        return "0.1"
