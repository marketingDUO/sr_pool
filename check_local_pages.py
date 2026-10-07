from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
from itertools import combinations
import json,re,hashlib,xml.etree.ElementTree as ET
root=Path(__file__).parent/'dist'
origin='https://sr-pool.de'
class Page(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[];self.h1=[];self.title=[];self.faqs=[];self.canonical=None;self.desc=None;self.schemas=[];self.state=[];self.text=[];self.in_main=False;self.in_script=False;self.json='';self.in_faq=False;self.current_q=None;self.current_a=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);self.state.append(tag)
  if tag=='main':self.in_main=True
  if tag=='script' and a.get('type')=='application/ld+json':self.in_script=True;self.json=''
  if tag=='link' and a.get('rel')=='canonical':self.canonical=a['href']
  if tag=='meta' and a.get('name')=='description':self.desc=a['content']
  if tag=='h1':self.h1.append('')
  if tag=='img':assert a.get('alt'),'Missing image alt'
  if a.get('id')=='faq':self.in_faq=True
  if self.in_faq and tag=='summary':self.current_q=''
  if self.in_faq and tag=='p':self.current_a=''
  for k in ['href','src']:
   if a.get(k,'').startswith('/') and not a[k].startswith('//'):self.links.append(a[k])
 def handle_endtag(self,tag):
  if tag=='main':self.in_main=False
  if tag=='script' and self.in_script:self.schemas.append(json.loads(self.json));self.in_script=False
  if self.in_faq and tag=='details' and self.current_q is not None:
   self.faqs.append((self.current_q,self.current_a));self.current_q=self.current_a=None
  if self.in_faq and tag=='div':self.in_faq=False
  while self.state:
   if self.state.pop()==tag:break
 def handle_data(self,data):
  if self.in_script:self.json+=data;return
  if 'h1' in self.state and self.h1:self.h1[-1]+=data
  if 'title' in self.state:self.title.append(data)
  if self.in_faq:
   if 'summary' in self.state and self.current_q is not None:self.current_q+=data
   elif 'p' in self.state and self.current_a is not None:self.current_a+=data
  if self.in_main:self.text.append(data)

allpages={};incoming={};titles=set();descs=set();canonical=set()
for f in root.rglob('index.html'):
 path='/'+str(f.parent.relative_to(root)).strip('/')+'/' if f.parent!=root else '/'
 p=Page();p.feed(f.read_text());allpages[path]=p
 assert len(p.h1)==1,(path,'h1 count',len(p.h1))
 assert p.canonical==origin+path,(path,'canonical')
 assert p.canonical not in canonical,(path,'repeated canonical');canonical.add(p.canonical)
 for link in p.links:
  route=urlparse(link).path;dest=root/route.lstrip('/')
  if route.endswith('/'):dest=dest/'index.html'
  assert dest.exists(),(path,'broken local link',link)
  incoming.setdefault(route,set()).add(path)
 if path.startswith('/poolbau/') and path!='/poolbau/':
  title=''.join(p.title);assert title not in titles,(path,'repeated title');titles.add(title)
  assert p.desc not in descs,(path,'repeated description');descs.add(p.desc)
  graph=p.schemas[0]['@graph'];faq=next(x for x in graph if 'FAQPage' in x.get('@type',[]))
  schema_answers=[(x['name'],x['acceptedAnswer']['text']) for x in faq['mainEntity']]
  assert p.faqs==schema_answers,(path,'FAQ markup differs from visible text')
  assert len(p.faqs)==3,(path,'FAQ count')
  org=next(x for x in graph if x.get('@type')=='HomeAndConstructionBusiness')
  assert org['address']['addressLocality']=='Berlin',path
  assert len(next(x for x in graph if x.get('@type')=='BreadcrumbList')['itemListElement']) in (3,4),path
cities=[x for x in allpages if x.startswith('/poolbau/') and x!='/poolbau/']
for path in cities:assert incoming.get(path),('orphan',path)
sitemap=ET.parse(root/'sitemap.xml');urls={x.text for x in sitemap.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
assert urls=={origin+p for p in allpages},'Sitemap mismatch'
# Compare authored planning text and FAQs after removing every place name.
blocks=Path(__file__).parent.joinpath('content/ortstexte.txt').read_text().strip().split('\n===\n')
names=[b.split('|',1)[0] for b in blocks]
docs=[]
for b in blocks:
 lines=b.splitlines();body=' '.join(lines[1:]).lower()
 for name in sorted(names,key=len,reverse=True):body=body.replace(name.lower(),'ort')
 words=re.findall(r'\w+',body);shingles={' '.join(words[i:i+5]) for i in range(len(words)-4)}
 docs.append((lines[0].split('|')[0],shingles,len(words)))
pairs=sorted(((len(a[1]&b[1])/min(len(a[1]),len(b[1])),a[0],b[0]) for a,b in combinations(docs,2)),reverse=True)
assert pairs[0][0]<.35,('High lexical overlap',pairs[0])
report={'place_pages':len(cities),'total_pages':len(allpages),'faq_answers':sum(len(allpages[p].faqs) for p in cities),'metadata_unique':True,'local_links_valid':True,'faq_markup_matches_visible_text':True,'sitemap_complete':True,'top_normalized_5word_overlap':[(round(x[0],3),x[1],x[2]) for x in pairs[:5]],'authored_words_per_page':{'min':min(x[2] for x in docs),'max':max(x[2] for x in docs)}}
Path(__file__).parent.joinpath('content/seo-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
