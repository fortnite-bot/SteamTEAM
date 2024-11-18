import json
read = open('./steam.json', 'r')
read2 = json.load(read)
print('\n', str(read2[0]['name']))