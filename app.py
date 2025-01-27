import json
import viktor as vkt

from viktor.external.python import PythonAnalysis
from io import BytesIO
from pathlib import Path
from viktor.core import File


def create_frame_data(length, height, cross_section = "IPE400"):
    nodes = {
        1: {"node_id": 1, "x": 0, "z": 0, "y": 0},
        2: {"node_id": 2, "x": 0, "z": length, "y": 0},
        3: {"node_id": 3, "x": 0, "z": 0, "y": height},
        4: {"node_id": 4, "x": 0, "z": length, "y": height},
        5: {"node_id": 5, "x": length, "z": 0, "y": 0},
        6: {"node_id": 6, "x": length, "z": length, "y": 0},
        7: {"node_id": 7, "x": length, "z": 0, "y": height},
        8: {"node_id": 8, "x": length, "z": length, "y": height},
    }
    lines = {
        1: {"line_id": 1, "node_i": 1, "node_j": 3},
        2: {"line_id": 2, "node_i": 2, "node_j": 4},
        3: {"line_id": 3, "node_i": 3, "node_j": 4},
        4: {"line_id": 4, "node_i": 6, "node_j": 8},
        5: {"line_id": 5, "node_i": 5, "node_j": 7},
        6: {"line_id": 6, "node_i": 3, "node_j": 7},
        7: {"line_id": 7, "node_i": 4, "node_j": 8},
        8: {"line_id": 8, "node_i": 7, "node_j": 8},
        9: {"line_id": 9, "node_i": 1, "node_j": 4},
        10:{"line_id": 10, "node_i": 5, "node_j":8},

    }

    with open("inputs.json","w") as jsonfile:
        json.dump([nodes, lines,cross_section], jsonfile) 
        
    return nodes, lines

class Parametrization(vkt.Parametrization):
    intro = vkt.Text("# STAAD - Member End Forces App")
    inputs_title = vkt.Text('''## Frame Geometry 
    Please fill in the following parameters to create the steel structure:''')
    frame_length = vkt.NumberField("Frame Length", min=0.3, default=8, suffix="sm")
    frame_height = vkt.NumberField("Frame Height", min=1, default=6, suffix="m")
    line_break = vkt.LineBreak()
    section_title = vkt.Text('''## Frame Cross-Section 
    Please select a cross section for the frame's elements:''')   
    cross_sect = vkt.OptionField("Cross-Section",options=["IPE400","IPE200"],default="IPE400")

class Controller(vkt.Controller):
    parametrization = Parametrization
    
    @vkt.GeometryView("3D Model", duration_guess=1,x_axis_to_right=True)
    def create_render(self, params, **kwargs):
        nodes, lines = create_frame_data(length=params.frame_length, height=params.frame_height)
        sections_group = []
        
        for line_id, dict_vals in lines.items():
            node_id_i = dict_vals["node_i"]
            node_id_j = dict_vals["node_j"]

            node_i = nodes[node_id_i]
            node_j = nodes[node_id_j]

            point_i = vkt.Point(node_i["x"], node_i["z"], node_i["y"])
            point_j = vkt.Point(node_j["x"], node_j["z"], node_j["y"])
            
            line_k = vkt.Line(point_i, point_j)
            cs_size = float(params.cross_sect[3:])/1000
            section_k = vkt.RectangularExtrusion(cs_size,cs_size, line_k, identifier=str(line_id))
            sections_group.append(section_k)
        return vkt.GeometryResult(geometry=sections_group)

    @vkt.TableView("Member End Forces",duration_guess=10, update_label="Run STAAD Analysis")
    def run_staad(self, params, **kwargs):
        nodes, lines = create_frame_data(length=params.frame_length, height= params.frame_height)
        cross_section = params.cross_sect
        input_json = json.dumps([nodes, lines,cross_section])
        script_path = Path(__file__).parent / "run_staad_model.py"
        print(script_path)
        script = File.from_path(script_path)

        files = [
        ("inputs.json", BytesIO(bytes(input_json, 'utf8'))),
        ]
        
        staad_analysis = PythonAnalysis(
            script =script,
            files=files,
            output_filenames=["output.json"]
        )
        staad_analysis.execute(timeout=300)
        output_file = staad_analysis.get_output_file("output.json")
        output_file = json.loads(output_file.getvalue())

        forces = [[round(force, 2) for force in row] for row in output_file['forces']]


        return vkt.TableResult(
            forces, 
            row_headers=output_file["headers"],
            column_headers=["FX [kN]", "FY [kN]", "FZ [kN] ", "MX [kN m]", "MY [kN m]","MZ [kN m]"],
        )