from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]
langs=['en','fr','ar','zh-CN','de'];catalog={lang:{} for lang in langs}
for line in (root/'Localizations/messages.tsv').read_text().splitlines():
 if not line:continue
 parts=line.split('|')
 assert len(parts)==5,(len(parts),parts[0])
 source=parts[0]
 assert source not in catalog['en'],source
 tokens=lambda x: sorted(re.findall(r'\{\w+\}',x))
 for lang,value in zip(langs,[source]+parts[1:]):
  assert value.strip(),(source,lang)
  assert tokens(source)==tokens(value),(source,lang)
  catalog[lang][source]=value
# Additional console locales have explicit English fallback for untranslated technical text.
extra=json.loads((root/'Localizations/additional.json').read_text())
for lang,values in extra.items():
 for key,value in values.items():
  assert key in catalog['en'],(lang,key)
  assert tokens(key)==tokens(value),(lang,key)
 catalog[lang]={**catalog['en'],**values}
for lang,base in {'en-US':'en','en-GB':'en','fr-FR':'fr','fr-CA':'fr','es-ES':'es','es-419':'es'}.items():catalog[lang]=catalog[base].copy()
_base={'en-US':'en','en-GB':'en','fr-FR':'fr','fr-CA':'fr','es-ES':'es','es-419':'es'}
def _authored(lang):
 src=_base.get(lang,lang)
 if src in langs:return len(catalog[src])
 return len(extra.get(src,{}))
coverage={lang:{'entries':len(catalog[lang]),'authored':_authored(lang), 'technical_fallback':_authored(lang)<len(catalog['en'])} for lang,label in json.loads((root/'Localizations/console-locales.json').read_text())}
(root/'Localizations/coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
(root/'Localizations/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
engine='''// BEGIN LOCALIZATION (generated from Localizations/messages.tsv)
var MESSAGES = __CATALOG__;
var locale = 'en', textBindings = [], attributeBindings = [];
function t(source, values) {
  var translated = (MESSAGES[locale] && MESSAGES[locale][source]) || source;
  return String(translated).replace(/\\{(\\w+)\\}/g, function (match, key) {
    return values && Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match;
  });
}
function bindTranslations() {
  var walker = document.createTreeWalker(document.body, 4, null, false), node;
  while ((node = walker.nextNode())) {
    var parent = node.parentElement, blocked = false;
    while (parent) {
      if (/^(SCRIPT|STYLE|PRE|CODE)$/.test(parent.tagName) || parent.id === 'language') { blocked = true; break; }
      parent = parent.parentElement;
    }
    var key = node.nodeValue.trim();
    if (!blocked && Object.prototype.hasOwnProperty.call(MESSAGES.en, key)) textBindings.push({node:node, source:node.nodeValue, key:key});
  }
  var elements = document.querySelectorAll('[aria-label], [title], [alt], [placeholder]');
  for (var i = 0; i < elements.length; i++) {
    ['aria-label','title','alt','placeholder'].forEach(function (attr) {
      var value = elements[i].getAttribute(attr);
      if (value && Object.prototype.hasOwnProperty.call(MESSAGES.en,value)) attributeBindings.push({node:elements[i],attr:attr,key:value});
    });
  }
}
function applyLanguage(requested, persist) {
  requested=({en:'en-US',fr:'fr-FR',no:'nb',zh:'zh-CN',pt:'pt-PT',es:'es-ES'})[requested]||requested;
  locale = MESSAGES[requested] ? requested : (MESSAGES[requested.split('-')[0]] ? requested.split('-')[0] : 'en-US');
  document.documentElement.lang = locale;
  document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
  $('language').value = locale;
  textBindings.forEach(function (binding) {
    if (document.documentElement.contains(binding.node)) binding.node.nodeValue = binding.source.replace(binding.key,t(binding.key));
  });
  attributeBindings.forEach(function (binding) { binding.node.setAttribute(binding.attr,t(binding.key)); });
  var elements = document.querySelectorAll('body *');
  for (var i = 0; i < elements.length; i++) {
    var source = elements[i]._translationSource;
    if (source != null) setText(elements[i], source);
  }
  var active = document.querySelector('.nav [aria-selected="true"]');
  setText($('page-title'), active.querySelector('span').firstChild.nodeValue, true);
  setText($('page-description'), active.querySelector('small').textContent, true);
  if (state) {
    renderChips(state.games || []); renderGrid(state.games || []); renderStorage(state.drives);
    renderWorkspace(); renderSettingsInfo();
    if ($('offline').classList.contains('show')) {
      setText($('connection'), 'Disconnected · data may be stale'); $('connection').classList.remove('online'); setText($('overview-payload'), 'Disconnected');
    }
    if (modalOpen()) renderModal();
  }
  if (persist) {
    try { localStorage.setItem('davinci-core-language',locale); setText($('language-status'),'Language saved in this browser.'); }
    catch (e) { setText($('language-status'),'Language applied for this session. Local storage is unavailable.'); }
  }
}
// END LOCALIZATION
'''.replace('__CATALOG__',json.dumps(catalog,ensure_ascii=False,separators=(',',':')))
p=root/'src/ui.html';s=p.read_text()
if '// BEGIN LOCALIZATION' in s:
 a=s.index('// BEGIN LOCALIZATION');b=s.index('// END LOCALIZATION',a)+len('// END LOCALIZATION')
 s=s[:a]+engine+s[b:]
else:
 s=s.replace("'use strict';","'use strict';\n"+engine,1)
 s=s.replace('<p class="language-note">Change', '<p class="language-note">Change',1)
 s=s.replace('The choice is saved in this browser.</p>', 'The choice is saved in this browser.</p><p id="language-status" class="language-note" role="status"></p>',1)
 s=s.replace("$('tab-dashboard').focus();\npoll();", """bindTranslations();
var initialLanguage = (navigator.language || 'en').toLowerCase().split('-')[0];
if (initialLanguage === 'zh') initialLanguage = 'zh-CN';
try { initialLanguage = localStorage.getItem('davinci-core-language') || initialLanguage; } catch (e) {}
applyLanguage(initialLanguage, false);
$('language').onchange = function () { applyLanguage(this.value, true); };
$('tab-dashboard').focus();
poll();""")
p.write_text(s)
(root/'review/ui-script.js').write_text(s.split('<script>')[1].split('</script>')[0])
_full=[k for k in langs if len(catalog[k])==len(catalog['en'])]+[k for k in extra if len(extra[k])==len(catalog['en'])]
_partial=[k for k in extra if len(extra[k])<len(catalog['en'])]
print('Catalog:',len(catalog['en']),'entries;',len(_full),'fully translated languages (%s)'%(', '.join(sorted(_full))),
      'plus %d partially translated languages (50 core labels each)'%len(_partial),'; placeholders validated')
