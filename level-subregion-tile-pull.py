import re
from typing import Type


def parse_level_dimensions(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    level_match = re.search(r'LEVEL\s*=\s*{(.*)}', content, re.DOTALL)
    if not level_match:
        raise ValueError("LEVEL block not found")
    level_content = level_match.group(1)
    _width = int(re.search(r'width\s*=\s*(\d+)', level_content).group(1))
    _height = int(re.search(r'height\s*=\s*(\d+)', level_content).group(1))

    return _width, _height

def parse_level_data(filepath, field="tiles", _type: Type = int):

    with open(filepath, 'r') as f:
        content = f.read()

    level_match = re.search(r'LEVEL\s*=\s*{(.*)}', content, re.DOTALL)
    if not level_match:
        raise ValueError("LEVEL block not found")
    level_content = level_match.group(1)

    tile_data_match = re.search(field+r'\s*=\s*\[([^\]]+)\]', level_content, re.DOTALL)
    if not tile_data_match:
        raise ValueError("tiles data not found")

    tile_data_str = tile_data_match.group(1)
    _tile_data = [_type(n.strip()) for n in tile_data_str.split(',') if n.strip()]

    return _tile_data

def extract_logic_gates_formatted(filepath, x1, y1, x2, y2):
    with open(filepath, 'r') as f:
        content = f.read()

    logic_match = re.search(r'LOGICGATES\s*=\s*{(.*?)}\s*$', content, re.DOTALL)
    if not logic_match:
        return "logicGates = {\n}"

    logic_block = logic_match.group(1)

    formatted_gates = []

    for match in re.finditer(r'LOGICGATE\s*=\s*{(.*?)}', logic_block, re.DOTALL):
        block = match.group(1)

        gate = {}
        for field_match in re.finditer(r'(\w+)\s*=\s*([^,\n]+)', block):
            key = field_match.group(1).strip()
            val = field_match.group(2).strip()
            if key in ("tileX", "tileY"):
                val = int(val)
            gate[key] = val

        if x1 <= gate["tileX"] < x2 and y1 <= gate["tileY"] < y2:
            gate["tileX"] -= x1
            gate["tileY"] -= y1

            gate_lines = [
                f'\t\ttileX = {gate["tileX"]}',
                f'\t\ttileY = {gate["tileY"]}',
                f'\t\tstringID = {gate["stringID"]}',
                f'\t\tmirrorX = false',
                f'\t\tmirrorY = false',
                f'\t\trotation = 0',
                f'\t\tdata = {{}}'
            ]
            gate_block = "\tgate = {\n" + ",\n".join(gate_lines) + "\n\t}"
            formatted_gates.append(gate_block)

    if not formatted_gates:
        return "logicGates = {\n}"

    return "logicGates = {\n" + ",\n".join(formatted_gates) + "\n}"


def build_tile_id_name_map(_tile_data, _tile_name_data):
    unique_ids = sorted(set(_tile_data))  # get unique tile IDs in use
    mapping = []

    for tile_id in unique_ids:
        try:
            tile_name = _tile_name_data[tile_id]
        except IndexError:
            tile_name = "UNKNOWN"
        mapping.extend([tile_id, tile_name])

    return mapping

def _flat(values, _width, _x1, _y1, _x2, _y2):
    flat = []
    for y in range(_y1, _y2):
        for x in range(_x1, _x2):
            index = y * _width + x
            flat.append(values[index])
    return flat

#.dat file where level data is saved
file_path = "-2696x504d0.dat"

# Desired region
x1, y1 = 144, 55
x2, y2 = 205, 99


width, height = parse_level_dimensions(file_path)

subregion_width = x2 - x1
subregion_height = y2 - y1


tile_data = _flat(parse_level_data(file_path, "tiles", int), width, x1, y1, x2, y2)
tile_name_data = parse_level_data(file_path, "tileData", str)

tile_map = build_tile_id_name_map(tile_data, tile_name_data)

object_data = _flat(parse_level_data(file_path, "objects", int), width, x1, y1, x2, y2)
object_name_data = parse_level_data(file_path, "objectData", str)

object_map = build_tile_id_name_map(object_data, object_name_data)

object_rotation_data = _flat(parse_level_data(file_path, "objectRotations", int), width, x1, y1, x2, y2)

logic_gates_data = extract_logic_gates_formatted(file_path, x1, y1, x2, y2)
wires_data = _flat(parse_level_data(file_path, "wire", int), width, x1, y1, x2, y2)

preset_script_builder = "PRESET = {"
preset_script_builder += f"\n\twidth = {subregion_width},"
preset_script_builder += f"\n\theight = {subregion_height},"

formatted_tile_map = str(tile_map).replace("'","")
preset_script_builder += f"\n\ttileIDs = {formatted_tile_map},"
preset_script_builder += f"\n\ttiles = {tile_data},"

formatted_object_map = str(object_map).replace("'","")
preset_script_builder += f"\n\tobjectIDs = {formatted_object_map},"
preset_script_builder += f"\n\tobjects = {object_data},"
preset_script_builder += f"\n\trotations = {object_rotation_data},"
preset_script_builder += f"\n\t{logic_gates_data},"
preset_script_builder += f"\n\twire = {wires_data}"
preset_script_builder += "\n}"

print(preset_script_builder)

with open("generated_preset", 'w') as f:
    f.write(preset_script_builder)