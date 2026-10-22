"""Script correction against measured ASR anchors, with explicit uncertainty."""
import difflib,re,unicodedata
from .core import require
from .voice_languages import script_comparison

def token(text):
    text=''.join(c for c in unicodedata.normalize('NFD',str(text).lower()) if unicodedata.category(c)!='Mn');return re.sub(r'[^\w]','',text)

def align_script(text,words,max_chars=68,max_cps=25,aliases=None):
    script=text.split();actual=[w for w in words if token(w['word'])];require(script and actual,'Script and measured words required')
    aliases={token(k):token(v) for k,v in (aliases or {}).items()}
    def norm(w):return aliases.get(token(w),token(w))
    matches={};a=[norm(w) for w in script];b=[norm(w['word']) for w in actual]
    for block in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for k in range(block.size):matches[block.a+k]=block.b+k
    groups=[];current=[];start=0
    for i,word in enumerate(script):
        if current and len(' '.join(current+[word]))>max_chars:groups.append((start,i-1,current));current=[];start=i
        current.append(word)
        if word.endswith(('.','?','!',';')):groups.append((start,i,current));current=[];start=i+1
    if current:groups.append((start,len(script)-1,current))
    cues=[]
    for left,right,parts in groups:
        found=[matches[i] for i in range(left,right+1) if i in matches];require(found,'Caption lacks measured anchor')
        start=max(float(actual[min(found)]['start']),cues[-1]['end'] if cues else 0);end=float(actual[max(found)]['end']);require(end>start,'Invalid caption')
        phrase=' '.join(parts);cps=len(phrase)/(end-start);coverage=len(found)/(right-left+1)
        cues.append({'start':round(start,3),'end':round(end,3),'text':phrase,'anchor_coverage':coverage,'cps':round(cps,2),
                     'review_required':cps>max_cps or coverage<1,'timing_source':'measured_word_anchors_script_corrected'})
    merged=[];i=0
    def join(a,b):
        text=a['text']+' '+b['text'];cps=len(text)/(b['end']-a['start']);coverage=min(a['anchor_coverage'],b['anchor_coverage'])
        return {**a,'end':b['end'],'text':text,'anchor_coverage':coverage,'cps':round(cps,2),'review_required':cps>max_cps or coverage<1}
    while i<len(cues):
        c=cues[i]
        if (len(c['text'])<16 or c['cps']>max_cps) and i+1<len(cues) and len(c['text']+' '+cues[i+1]['text'])<=76:c=join(c,cues[i+1]);i+=1
        if len(c['text'])<16 and merged and len(merged[-1]['text']+' '+c['text'])<=76:c=join(merged.pop(),c)
        merged.append(c);i+=1
    return merged

def pronunciation_review(expected,actual,language='Spanish',glossary=None):
    return {'script_comparison':script_comparison(expected,actual,language),
            'terms':[{'term':k,'spoken_hint':v,'recognizer_found':token(k) in token(actual),'listening_review':'pending'} for k,v in (glossary or {}).items() if k.casefold() in expected.casefold()],
            'phonetic_quality':'not measured','regional_identity':'requires audition','approved':False}
