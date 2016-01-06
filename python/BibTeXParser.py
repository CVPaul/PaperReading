#!/usr/bin/env python
# 
# Copyright 2012, Karljohan Lundin Palmerius
# 
# Usage:
# 
# import BibTeXParser
# parser = BibTeXParser()
# result = parser.parse("bibliography.bib")
# 
# The result will be a list of one associative array for each bibtex
# record, containing the fields "type" and "key" with record type and
# bibtex-key, respectively, and the fields of each record.
# 

import re

re_head_pattern = """\s*(\w+)\s*[({]\s*(\w*)\s*"""
re_var_pattern = """\s*(\w+)\s*=\s*(.*)\s*,?"""

class BibTeXParser:
  
  def __init__(self):
    pass

  def parse(self,filename):
    
    file_contents = None
    with open(filename,"r") as fin:
      file_contents = fin.read()
    
    if file_contents is None:
      return None
    
    records = file_contents.split("@")
    re_head = re.compile(re_head_pattern)
    re_var = re.compile(re_var_pattern)
    
    result = []
    
    for record in records:
      
      lines = record.splitlines()
      if len(lines) < 2: continue
      
      head_res = re_head.match(lines[0])
      del lines[0]

      res_rec = { "type": head_res.group(1), "key": head_res.group(2) }
      
      for line in lines:
        var_res = re_var.match(line)
        if var_res is None: continue
        res_rec[var_res.group(1)] = var_res.group(2).strip("""}"{,""")
        
      result.append(res_rec)

    return result

  def parse_str(self,bibstr):
    
    file_contents = bibstr
    
    if file_contents is None:
      return None
    
    records = file_contents.split("@")
    re_head = re.compile(re_head_pattern)
    re_var = re.compile(re_var_pattern)
    
    result = []
    
    for record in records:
      
      lines = record.splitlines()
      if len(lines) < 2: continue
      
      head_res = re_head.match(lines[0])
      del lines[0]

      res_rec = { "type": head_res.group(1), "key": head_res.group(2) }
      
      for line in lines:
        var_res = re_var.match(line)
        if var_res is None: continue
        res_rec[var_res.group(1)] = var_res.group(2).strip("""}"{,""")
        
      result.append(res_rec)

    return result

