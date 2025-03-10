# /mnt/home2/mud/systems/nroff.py
# Imported to: help_files.py, object.py
# Imports from: driver.py

from typing import List, Optional, Dict, Any
from ..driver import driver, MudObject
import os
import json
import re

V_HEADER, V_CENTER, V_ALL, V_INDENT, V_PARA, V_LEFT, V_TABLE, V_COLUMN = range(8)

class NroffHandler:
    def __init__(self):
        self.nroffed_file: List[Any] = []  # Mixed list of strings and formatting directives
        self.nroffed_file_name = ""
        self.modified_time = 0

    def cat_file(self, fname: str, update: bool = False) -> Optional[str]:
        if not os.path.exists(fname):
            return None
        if update:
            with open(fname, 'r') as f:
                data = json.load(f)
                self.nroffed_file_name = data.get("nroffed_file_name", "")
                self.modified_time = data.get("modified_time", 0)
                self.nroffed_file = data.get("nroffed_file", [])
            if not self.nroffed_file_name or os.path.getmtime(self.nroffed_file_name) > self.modified_time:
                return None
        cols = driver.this_player().attrs.get("cols", 79) if driver.this_player() else 79
        ret = " \n"
        i = 0
        while i < len(self.nroffed_file):
            if isinstance(self.nroffed_file[i], str):
                ret += self.nroffed_file[i]
            else:
                if self.nroffed_file[i] == V_HEADER:
                    ret += f"\033[1m{self.nroffed_file[i+1]}\033[0m\n"
                    i += 1
                elif self.nroffed_file[i] == V_CENTER:
                    ret += f"{self.nroffed_file[i+1]:^{cols}}\n"
                    i += 1
                elif self.nroffed_file[i] == V_ALL:
                    left, center, right = self.nroffed_file[i+2:i+5]
                    width = self.nroffed_file[i+1]
                    ret += f"\033[1m\n{left:<{width}}{center:^{cols-2*width}}{right:>{width}}\n\033[0m\n"
                    i += 4
                elif self.nroffed_file[i] == V_INDENT:
                    indent = self.nroffed_file[i+1]
                    ret += f"{' '*indent}{self.nroffed_file[i+2]:<{cols-indent}}\n"
                    i += 2
                elif self.nroffed_file[i] == V_PARA:
                    left_indent, right_indent, text = self.nroffed_file[i+1:i+4]
                    if left_indent:
                        ret += f"{' '*left_indent}{text:<{cols-left_indent-right_indent}}{' '*right_indent}\n"
                    elif right_indent:
                        ret += f"{text:<{cols-right_indent}}{' '*right_indent}\n"
                    else:
                        ret += f"{text:<{cols}}\n"
                    i += 3
                elif self.nroffed_file[i] == V_LEFT:
                    ret += f"{self.nroffed_file[i+1]:<{cols}}\n"
                    i += 1
                elif self.nroffed_file[i] == V_TABLE:
                    ret += f"{self.nroffed_file[i+1]}\n"
                    i += 1
                elif self.nroffed_file[i] == V_COLUMN:
                    col_widths = self.nroffed_file[i+1]
                    cols_data = self.nroffed_file[i+2:i+2+len(col_widths)]
                    for j in range(len(cols_data[0])):
                        line = "".join(f"{cols_data[k][j]:<{col_widths[k]}}" for k in range(len(col_widths)))
                        ret += f"{line.rstrip()}\n"
                    i += len(col_widths) + 1
            i += 1
        return ret

    def html_file(self, file: str, title: str) -> Optional[str]:
        if not os.path.exists(file):
            return None
        with open(file, 'r') as f:
            data = json.load(f)
            self.nroffed_file = data.get("nroffed_file", [])
        ret = f"<html><head><title>{title}</title></head><body>"
        in_bold = in_italic = False
        i = 0
        while i < len(self.nroffed_file):
            if isinstance(self.nroffed_file[i], str):
                ret += f"<h3>{self.htmlify(self.nroffed_file[i])}</h3>"
            else:
                if self.nroffed_file[i] == V_HEADER:
                    ret += f"<h3>{self.htmlify(self.nroffed_file[i+1])}</h3>"
                    i += 1
                elif self.nroffed_file[i] == V_CENTER:
                    ret += f"<center>{self.htmlify(self.nroffed_file[i+1])}</center>"
                    i += 1
                elif self.nroffed_file[i] == V_ALL:
                    left, center, right = self.nroffed_file[i+2:i+5]
                    ret += f"<table width='100%'><tr><td align='left'><h2>{left}</h2></td><td align='center'><h2>{center}</h2></td><td align='right'><h2>{right}</h2></td></tr></table>"
                    i += 4
                elif self.nroffed_file[i] == V_INDENT:
                    ret += self.htmlify(self.nroffed_file[i+2])
                    i += 2
                elif self.nroffed_file[i] == V_PARA:
                    ret += f"<p>{self.htmlify(self.nroffed_file[i+3])}</p>"
                    i += 3
                elif self.nroffed_file[i] == V_LEFT:
                    ret += f"<div align='left'>{self.htmlify(self.nroffed_file[i+1])}</div>"
                    i += 1
                elif self.nroffed_file[i] == V_TABLE:
                    ret += f"<ul><li>{self.htmlify(self.nroffed_file[i+1].replace('\n', '<li>'))}</ul>"
                    i += 1
                elif self.nroffed_file[i] == V_COLUMN:
                    ret += "<table cellpadding='10'>"
                    col_widths = self.nroffed_file[i+1]
                    cols_data = self.nroffed_file[i+2:i+2+len(col_widths)]
                    for j in range(len(cols_data[0])):
                        ret += "<tr>" + "".join(f"<td>{self.htmlify(cols_data[k][j])}</td>" for k in range(len(col_widths))) + "</tr>"
                    ret += "</table>"
                    i += len(col_widths) + 1
            i += 1
        if in_bold:
            ret += "</strong>"
        if in_italic:
            ret += "</i>"
        ret += "</body></html>"
        return ret

    def htmlify(self, str_: str) -> str:
        str_ = re.sub(r'\*([^*]+)\*', r'<strong>\1</strong>', str_)  # Markdown bold
        return str_.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    def create_nroff(self, in_file: str, out_file: str) -> bool:
        if not os.path.exists(in_file):
            return False
        self.nroffed_file_name = in_file
        self.modified_time = int(os.path.getmtime(in_file))
        with open(in_file, 'r') as f:
            text = f.read()
        bits = ["#" + line for line in text.split('\n')]  # Simulate LPC explode behavior
        bits[0] = bits[0][1:]
        self.nroffed_file = [0]
        if bits[0]:
            self.add_string(bits[0])
        strip_crs = col_mode = conv_tabs = new_string = force_string = 0
        cols: List[List[str]] = []
        num_cols = 0
        for i in range(1, len(bits)):
            tmp = bits[i].split("\n", 1)
            fluff = len(tmp) == 1
            directive = tmp[0][2:] if not fluff else bits[i][2:]
            content = tmp[1] if not fluff else ""

            if directive.startswith("SH"):
                self.add_int(V_HEADER)
                self.add_string(directive[3:])
                new_string = 1
            elif directive.startswith("SI"):
                self.add_int(V_INDENT)
                indent = int(re.search(r'\d+', directive[2:]) or 0)
                self.add_int(indent)
                force_string = 1
            elif directive.startswith("EI"):
                self.add_string("")
                new_string = 1
            elif directive.startswith("SP"):
                self.add_int(V_PARA)
                parts = re.findall(r'\d+', directive[2:]) or [0, 0]
                self.add_int(int(parts[0]))
                self.add_int(int(parts[1]) if len(parts) > 1 else 0)
                force_string = 1
                strip_crs = 1
            elif directive.startswith("EP"):
                self.add_string("")
                new_string = 1
                strip_crs = 0
            elif directive.startswith("SC"):
                self.add_int(V_CENTER)
                force_string = 1
            elif directive.startswith("EC"):
                new_string = 1
            elif directive.startswith("SL"):
                self.add_int(V_LEFT)
                force_string = 1
            elif directive.startswith("EL"):
                new_string = 1
            elif directive.startswith("ST"):
                self.add_int(V_TABLE)
                force_string = 1
                conv_tabs = 1
            elif directive.startswith("ET"):
                new_string = 1
                conv_tabs = 0
            elif directive.startswith("DT"):
                bing = content.split("\n")[:3]
                if len(bing) < 3:
                    return False
                self.add_int(V_ALL)
                self.add_int(max(len(bing[0]), len(bing[2])))
                for line in bing[:3]:
                    self.add_string(line)
                    new_string = 1
                bits[i] = "\n".join(content.split("\n")[3:])
            elif directive.startswith("SO"):
                cols = [int(x) for x in re.findall(r'\d+', directive[2:])]
                num_cols = len(cols)
                self.add_int(V_COLUMN)
                self.add_array(cols)
                cols = [[] for _ in range(num_cols)]
                col_mode = 1
            elif directive.startswith("EO"):
                for j in range(num_cols):
                    self.add_array(cols[j])
                col_mode = 0
            elif directive.startswith("NF"):
                new_file = content.split("\n")[0]
                if not os.path.exists(new_file):
                    return False
                with open(new_file, 'r') as f:
                    text = f.read()
                bits = ["#" + line for line in text.split('\n')]
                bits[0] = bits[0][1:]
                self.nroffed_file = [0]
                if bits[0]:
                    self.add_string(bits[0])
                strip_crs = col_mode = conv_tabs = i = 0

            if fluff:
                continue
            if conv_tabs:
                bits[i] = bits[i].replace("\t", "\n")
            if col_mode:
                lines = bits[i].split("\n")
                for line in lines:
                    bing = ["#" + x for x in line.split("\t")]
                    bing[0] = bing[0][1:]
                    for j in range(num_cols):
                        cols[j].append(bing[j] if j < len(bing) else "\n")
            elif strip_crs:
                bits[i] = re.sub(r'\n\n', '$%^NeW_LiNe^%$', bits[i])
                bits[i] = re.sub(r'\.\n', '.  ', bits[i])
                bits[i] = re.sub(r'\n', ' ', bits[i])
                bits[i] = re.sub(r'\$%^NeW_LiNe^%\$', '\n\n', bits[i])
                self.add_string(bits[i] + " ")
            else:
                self.add_string(bits[i] + "\n")
        with open(out_file, 'w') as f:
            json.dump({"nroffed_file_name": self.nroffed_file_name, "modified_time": self.modified_time, "nroffed_file": self.nroffed_file}, f)
        return True

    def add_array(self, i: List[Any]):
        if not self.nroffed_file or force_string:
            self.nroffed_file.extend(["", i])
        else:
            self.nroffed_file.append(i)
        global force_string, new_string
        force_string = new_string = 0

    def add_int(self, i: int):
        if not self.nroffed_file or force_string:
            self.nroffed_file.extend(["", i])
        else:
            self.nroffed_file.append(i)
        global force_string, new_string
        force_string = new_string = 0

    def add_string(self, s: str):
        global new_string, force_string
        if not self.nroffed_file or new_string:
            self.nroffed_file.append(s)
        elif isinstance(self.nroffed_file[-1], str):
            self.nroffed_file[-1] += s
        else:
            self.nroffed_file.append(s)
        new_string = force_string = 0

    def query_file_name(self, fname: str) -> Optional[str]:
        if not os.path.exists(fname):
            return None
        with open(fname, 'r') as f:
            data = json.load(f)
            return data.get("nroffed_file_name", "")

async def init(driver_instance):
    global NROFF_HAND
    driver = driver_instance
    NROFF_HAND = NroffHandler()
    driver.nroff_handler = NROFF_HAND