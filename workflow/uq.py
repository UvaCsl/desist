import pathlib
import os
import pandas as pd
import subprocess

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

        # add "/." to copy contents including hidden directories
        subprocess.run(["cp", "-r", f"{str(orig)}/.", copy])

        # load the template patient configuration
        patient = Patient.from_yaml(self.template_fname)

        # change its filename
        patient.dir = pathlib.Path(target_dir).absolute()

        # update parameters
        patient.update(**params)

        # dump patient to yaml and xml
        patient.to_yaml()
        patient.to_xml()

    def _log_substitution_failure(self, exception):
        # TODO
        pass

    def get_restart_dict(self):
        # TODO: temporary to fill requirement of returning some dict
        return {"target_filename": self.target_filename,
                "template_fname": self.template_fname}

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

        patient = Patient.from_yaml(run_path.joinpath(self.target_filename))

        data = []

        #for col in self.output_columns:
        #    if isinstance(col, str):
        #        data.append([(col, 0), [1])

        data = [(("age"), 50), (("HeartRate"), 100)]
        return pd.DataFrame(data)

    def _log_substitution_failure(self, exception):
        # TODO
        pass

    def get_restart_dict(self):
        # TODO: temporary to fill requirement of returning some dict
        return {"target_filename": self.target_filename,
                "output_columns": self.output_columns}

    def element_version(self):
        # TODO: temporary to fill required function
        return "0.1"
