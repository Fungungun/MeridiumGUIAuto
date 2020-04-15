'''
This script extracts the error log for manual fix from the ASI tool log

__author__ = "Chenghuan Liu"
__email__ = "chenghuan.liu@woodplc.com" 
'''
import re

import argparse

parser = argparse.ArgumentParser(description='extracts the error log for manual fix from the ASI tool log')
parser.add_argument('--site_number')

args = parser.parse_args()


site_number = args.site_number
print(f"Extract error log for site {site_number}")

input_file = f"log/{site_number}.log"
output_file = f"log/{site_number}_error.log"

targeted_pattern = [r'Start processing package', r'Adding.+job_plan.+', r'link.+to this job plan', r'.+not in action name list.+Skip this action']

with open(output_file, 'w') as fo:
    with open(input_file, 'r') as fr:
        for line in fr:
            if 'ERROR' in line:
                continue
            line = line.split('INFO')[1] # remove the time and info 
            
            for p in targeted_pattern:
                match = re.search(p, line)
                if match:
                    fo.write(match.string)
                    

    