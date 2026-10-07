from pathlib import Path
from html import escape
from urllib.parse import urlencode
import ast, json, re, hashlib
from itertools import combinations

project=Path(__file__).parent
root=project/'dist'
# Reuse the site's current header, footer, layout and build without altering imagery.
import build_site as site

def slug(name):
 s=name.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
 s=s.replace(' (havel)','-havel').replace('/','-').replace(' bei berlin','')
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')

def url(name):return '/poolbau/'+slug(name)+'/'

records=[]
for block in (project/'content/ortstexte.txt').read_text().strip().split('\n===\n'):
 lines=block.strip().splitlines()
 assert len(lines)==8,(lines[0],len(lines))
 name,headline=lines[0].split('|',1)
 sections=[x.split('|',1) for x in lines[2:4]]
 faqs=[x.split('~',1) for x in lines[5:8]]
 records.append({'name':name,'headline':headline,'intro':lines[1],'sections':sections,'checks':lines[4].split(';'),'faqs':faqs})
by_name={x['name']:x for x in records}
expected=['Berlin']+[name for r in site.regions for name in r[3]]
assert sorted(by_name)==sorted(expected),'Place coverage mismatch'
assert len({slug(n) for n in expected})==len(expected),'URL collision'
regions_by_place={n:r for r in site.regions for n in r[3]}

for index,d in enumerate(records):
 name=d['name'];route=url(name);region=regions_by_place.get(name)
 image_name=['pool-hero.webp','pool-types.webp','pool-garden.webp','pool-detail.webp'][index%4]
 crumbs=[('Startseite','/'),('Einsatzgebiet','/einsatzgebiet/')]
 if region:crumbs.append((region[2],'/einsatzgebiet/'+region[0]+'/'))
 crumbs.append((name,route))
 breadcrumb='<nav class="breadcrumbs wrap" aria-label="Brotkrumennavigation">'+''.join((f'<span aria-current="page">{escape(label)}</span>' if i==len(crumbs)-1 else f'<a href="{link}">{escape(label)}</a>') for i,(label,link) in enumerate(crumbs))+'</nav>'
 body=breadcrumb+site.intro(escape(d['headline']),escape(d['intro']),'SR POOL · '+escape(name.upper()))
 body+='<section class="wrap local-intro-grid"><div class="local-intro-photo">'+site.image(image_name,'Pool-Inspiration mit Gartenbepflanzung und Terrasse')+'</div><aside class="local-checks"><h2>Ihre Beratung vorbereiten</h2><ul>'+''.join('<li>'+escape(c)+'</li>' for c in d['checks'])+'</ul>'+site.btn('Poolprojekt in '+name+' besprechen','/kontakt/?'+urlencode({'ort':name}))+'<p class="note">SR Pool · SR Bau GmbH<br>Kontaktstandort: Berlin-Kaulsdorf<br>Telefon: <a href="tel:+4915111150592">0151 111 50 592</a></p></aside></section>'
 body+='<section class="wrap section local-content"><div class="local-text-grid">'+''.join('<article><h2>'+escape(h)+'</h2><p>'+escape(p)+'</p></article>' for h,p in d['sections'])+'</div><div class="local-service-links"><a href="/poolarten/">Beckenarten vergleichen</a><a href="/poolbau/">Beratung und Bauablauf</a><a href="/pflege-wartung/">Poolpflege und Wartung</a></div></section>'
 body+='<section class="pale local-faq-section"><div class="wrap narrow"><p class="eyebrow">ANTWORTEN ZU IHREM POOLPROJEKT</p><h2>FAQ zum Poolbau in '+escape(name)+'</h2><div id="faq">'+''.join('<details><summary>'+escape(q)+'</summary><p>'+escape(a)+'</p></details>' for q,a in d['faqs'])+'</div></div></section>'
 peers=region[3] if region else ['Wandlitz','Oranienburg','Erkner','Falkensee']
 peers=[n for n in peers if n!=name]
 if region:
  pos=region[3].index(name);peers=(region[3][pos+1:]+region[3][:pos])[:4]
 body+='<section class="wrap local-related"><h2>Weitere Orte im Einsatzgebiet</h2><div>'+''.join(f'<a href="{url(n)}">Poolbau in {escape(n)}</a>' for n in peers)+'</div></section>'
 body+='<section class="cta"><div class="wrap cta-inner"><div><p class="eyebrow">IHR PROJEKT IN '+escape(name.upper())+'</p><h2>Gemeinsam den nächsten<br>Schritt planen.</h2><p>Besprechen Sie Ihre Gartenidee, gewünschte Beckenart und Ausstattung direkt mit SR Pool.</p></div>'+site.btn('Beratung anfragen','/kontakt/?'+urlencode({'ort':name}))+'</div></section>'
 desc=d['intro'].split('. ')[0].rstrip('.')+'. Beratung, Poolbau und Wartung mit SR Pool.'
 # Keep descriptions readable, never cut a word to hit an arbitrary character target.
 if len(desc)>185:desc=d['intro'].split('. ')[0].rstrip('.')+'.'
 site.page('poolbau/'+slug(name),d['headline'],desc,body)
 file=root/'poolbau'/slug(name)/'index.html'
 html=file.read_text()
 main_url=site.origin+route
 org_id=site.origin+'/#unternehmen'
 # All schemas describe the visible business and service; the actual address stays in Berlin.
 business=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',html).group(1))
 business['@id']=org_id
 business['logo']=site.origin+'/assets/sr-pool-logo.png'
 business['openingHoursSpecification']=[{'@type':'OpeningHoursSpecification','dayOfWeek':['Monday','Tuesday','Wednesday','Thursday','Friday'],'opens':'08:00','closes':'16:00'}]
 service={'@type':'Service','@id':main_url+'#service','name':'Poolbau in '+name,'serviceType':'Beratung, Poolbau, Pflege und Wartung','provider':{'@id':org_id},'areaServed':{'@type':'Place','name':name},'url':main_url,'description':d['intro']}
 graph={'@context':'https://schema.org','@graph':[business,service,{'@type':['WebPage','FAQPage'],'@id':main_url+'#webpage','url':main_url,'name':d['headline'],'description':desc,'inLanguage':'de-DE','about':{'@id':main_url+'#service'},'breadcrumb':{'@id':main_url+'#breadcrumb'},'mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in d['faqs']]},{'@type':'BreadcrumbList','@id':main_url+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i+1,'name':label,'item':site.origin+link} for i,(label,link) in enumerate(crumbs)]}]}
 html=re.sub(r'<script type="application/ld\+json">.*?</script>',lambda _: '<script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False)+'</script>',html,count=1)
 html=html.replace('<meta name="theme-color"','<meta name="robots" content="index,follow,max-image-preview:large"><meta name="theme-color"',1)
 file.write_text(html)

# Link directory from all existing pages without making the header or homepage visually busier.
for file in root.rglob('index.html'):
 html=file.read_text()
 html=html.replace('<a href="/einsatzgebiet/">Berlin & Umland</a>','<a href="/einsatzgebiet/">Alle Orte · Berlin & Umland</a>')
 file.write_text(html)

for region in site.regions:
 file=root/'einsatzgebiet'/region[0]/'index.html';html=file.read_text()
 town_links='<section class="wrap local-directory compact-faq"><details><summary>Poolbau in den Orten dieser Region</summary><div class="town-directory">'+''.join(f'<a href="{url(n)}">{escape(n)}</a>' for n in region[3])+'</div></details></section>'
 html=html.replace('</main>',town_links+'</main>');file.write_text(html)

hub=root/'einsatzgebiet/index.html';html=hub.read_text()
groups='<section class="wrap local-directory section-tight"><h2>Poolbau an Ihrem Ort</h2><p>Informationen zur Planung und häufige Fragen für die Orte in unserem Einsatzgebiet.</p><div class="directory-groups"><details><summary>Berlin</summary><div class="town-directory"><a href="'+url('Berlin')+'">Poolbau in Berlin</a></div></details>'
for region in site.regions:
 groups+='<details><summary>'+escape(region[2])+'</summary><div class="town-directory">'+''.join(f'<a href="{url(n)}">{escape(n)}</a>' for n in region[3])+'</div></details>'
groups+='</div></section>'
html=html.replace('<section class="cta">',groups+'<section class="cta">',1);hub.write_text(html)

# Carry the project town into the existing, clearly disclosed email preparation flow.
js_file=root/'assets/site.js';js=js_file.read_text();needle="const pool=params.get('pool');"
js=js.replace(needle,"const town=params.get('ort');if(town)document.querySelector('#place').value=town.slice(0,120);"+needle,1);js_file.write_text(js)

css='''\n.breadcrumbs{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.85rem;color:#526d7d;padding-top:25px}.breadcrumbs a{border-bottom:1px solid #bdd3df}.breadcrumbs span{color:#213e50}.local-intro-grid{display:grid;grid-template-columns:1.4fr 1fr;gap:40px;align-items:stretch}.local-intro-photo .photo{height:400px}.local-checks{padding:32px;background:#f2f7fa}.local-checks h2{font-size:1.5rem;line-height:1.25}.local-checks ul{padding-left:20px;margin:20px 0 25px;color:#486577}.local-checks li{margin:8px 0}.local-checks .btn{width:100%}.local-text-grid{display:grid;grid-template-columns:1fr 1fr;gap:55px}.local-text-grid h2{font-size:2rem;line-height:1.2}.local-text-grid p{margin-top:24px;line-height:1.8}.local-service-links{display:flex;flex-wrap:wrap;gap:15px 30px;border-top:1px solid #d0e0e9;margin-top:40px;padding-top:22px;color:#076d9e;font-weight:600;font-size:.95rem}.local-service-links a:hover{text-decoration:underline}.local-faq-section{padding:55px 0}.local-faq-section h2{font-size:2.15rem;line-height:1.2;margin-bottom:25px}.local-faq-section summary{font-size:1.05rem}.local-related{padding:35px 0 50px}.local-related h2{font-size:1.1rem;letter-spacing:0;margin-bottom:18px}.local-related>div,.town-directory{display:flex;flex-wrap:wrap;gap:12px 25px}.local-related a,.town-directory a{color:#076d9e;font-size:.95rem;border-bottom:1px solid #c4dbe8;padding-bottom:3px}.town-directory{padding:20px 0 5px}.directory-groups{margin-top:25px}.local-directory h2{font-size:1.8rem}.local-directory h2+p{margin-top:15px}.local-directory summary{font-size:1rem}@media(max-width:750px){.local-intro-grid,.local-text-grid{grid-template-columns:1fr;gap:30px}.local-intro-photo .photo{height:300px}.local-checks{padding:25px}.local-text-grid h2{font-size:1.8rem}.local-faq-section{padding:40px 0}.local-faq-section h2{font-size:1.9rem}.breadcrumbs{font-size:.8rem;gap:7px 13px}.local-related>div,.town-directory{gap:12px 20px}}\n'''
with (root/'assets/site.css').open('a') as f:f.write(css)
paths=sorted('/'+str(p.parent.relative_to(root)).strip('/')+'/' if p.parent!=root else '/' for p in root.rglob('index.html'))
(root/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+site.origin+path+'</loc></url>' for path in paths)+'</urlset>')
print('Built',len(records),'individual place pages;',len(paths),'total pages')
