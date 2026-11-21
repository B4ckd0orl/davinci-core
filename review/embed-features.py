from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'src/ui.html';s=p.read_text();a=s.index('// BEGIN DAVINCI FEATURES');b=s.index('// END DAVINCI FEATURES',a)+len('// END DAVINCI FEATURES')
files=['update-policy.js','updates-client.js','installed-management.js']
p.write_text(s[:a]+'// BEGIN DAVINCI FEATURES\n'+'\n'.join((root/'review'/n).read_text().strip() for n in files)+'\n// END DAVINCI FEATURES'+s[b:])
