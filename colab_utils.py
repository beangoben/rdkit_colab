"""Collections of functions for running colab kernels."""
import glob
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import urllib.request
from typing import List, Text

import IPython.display
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import yaml

# Assumes miniconda3 latests is 3.7, might have to update if it changes.
CONDA_DIR = '/usr/local/lib/python3.7/site-packages/'
IN_COLAB = 'google.colab' in sys.modules
CONDA_URL = 'https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh'

def add_conda_dir_to_python_path():
    """Add CONDA_DIR to sys.path."""
    sys.path.append(CONDA_DIR)

def is_running_colab()-> bool:
    """Check if running colab"""
    return 'google.colab' in sys.modules


def pip_install(package_list, force=False):
    extra = '--upgrade --force-reinstall' if force else ''
    [run_cmd(f'pip install {extra} {p}') for p in package_list]

def pip_install_from_conda_yaml(filename='environment.yml', force=False):
    pip_config = None
    with open(filename,'r') as afile:
        config = yaml.load(afile)
        assert 'dependencies' in config, f'{filename} is not a valid conda yaml'
        for item in config['dependencies']:
            if isinstance(item, dict) and item['pip'] is not None:
                pip_config = item['pip']
    assert pip_config is not None, f'Did not find pip in {filename}'
    pip_install(pip_config, force=force)

def run_cmd(cmd: Text, split: bool=True, shell=False, verbose: bool=True):
    """Run a system command and print output."""
    print(f'CMD: {cmd}')
    cmd = shlex.split(cmd) if split else [cmd]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=shell)
    while True:
        output = process.stdout.readline().decode('utf-8').strip()
        if output == '' and process.poll() is not None:
            break
        if output and verbose:
            print(output)
    return_code = process.poll()
    if return_code != 0:
        print(f'\tERROR ({return_code}) running command!')
    return return_code


def run_cmd_list(cmd_list: List[Text]):
    """Run several commands."""
    list(map(run_cmd, cmd_list))


def clone_repo(repo_url: Text)-> None:
    """Clone github repo and move to main dir."""
    repo_dir = repo_url.split('/')[-1].replace('.git', '')
    run_cmd(f'git clone {repo_url}', split=False, shell=True)
    # mv {repo_dir}/* to .
    for afile in glob.glob(f'{repo_dir}/*'):
        shutil.move(afile, '.')
    shutil.rmtree(repo_dir)


def copy_ssh_key(id_rsa_url: Text)->None:
    """Copy ssh keys for private repos."""
    key_dir = "/root/.ssh"
    key_path = os.path.join(key_dir, 'id_rsa')
    pathlib.Path(key_dir).mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(id_rsa_url, key_path)
    os.chmod(key_path, 0o400)
    # Same as 'ssh-keyscan github.com >> {key_dir}/known_hosts'
    text = subprocess.check_output(['ssh-keyscan', 'github.com'])
    with open(os.path.join(key_dir, 'known_hosts'), 'wb') as afile:
        afile.write(text)


def install_rdkit(force=False):
    conda_sh = CONDA_URL.split('/')[-1]
    cmd_list = [
        f"wget -c {CONDA_URL}",
        f"chmod +x {conda_sh}",
        f"bash ./{conda_sh} -b -f -p /usr/local",
        "conda install -q -y -c conda-forge rdkit",
        f"rm -rf {conda_sh}"]
    if IN_COLAB and not os.path.exists(CONDA_DIR) and not force:
        run_cmd_list(cmd_list)
        print(f'Restart your runtime and append "{CONDA_DIR}" to sys.path!')


def matplotlib_settings():
    """"Change matplotlib settings."""
    sns.set_style("white")
    sns.set_style('ticks')
    sns.set_context("paper", font_scale=2.25)
    sns.set_palette(sns.color_palette('bright'))

    params = {'savefig.dpi': 100,
              'lines.linewidth': 3,
              'axes.linewidth': 2.5,
              'savefig.dpi': 300,
              'xtick.major.width': 2.5,
              'ytick.major.width': 2.5,
              'xtick.minor.width': 1,
              'ytick.minor.width': 1,
              'font.weight': 'medium',
              'figure.figsize': (12, 8)
              }

    mpl.rcParams.update(params)
    IPython.display.set_matplotlib_formats('retina')
