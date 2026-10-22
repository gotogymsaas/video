"""Explicit language plans and script checks; these do not certify pronunciation."""
from __future__ import annotations
import math,re,unicodedata
from .core import require


LANGUAGES={'Auto':None,'Spanish':'es','English':'en','Portuguese':'pt','French':'fr',
           'Italian':'it','German':'de','Chinese':'zh','Japanese':'ja','Korean':'ko','Russian':'ru'}


def normalize_language(value):
    require(isinstance(value,str),'Language must be a name or ISO code')
    for name,code in LANGUAGES.items():
        if value.strip().casefold() in [name.casefold(),code]:return name
    require(False,'Unsupported language; choose '+', '.join(LANGUAGES))


def speech_plan(text,language='Spanish',segments=None):
    """Choose one target language or ordered phrases, keeping the reference separate."""
    default=normalize_language(language)
    if segments is None:
        require(isinstance(text,str) and text.strip(),'Enter a script')
        parts=[{'text':text.strip(),'language':default}]
    else:
        require(isinstance(text,str) and not text.strip(),'Use text or language segments, not both')
        require(isinstance(segments,list) and 1<=len(segments)<=24,'Use 1–24 language phrases')
        parts=[]
        for item in segments:
            require(isinstance(item,dict) and isinstance(item.get('text'),str) and item['text'].strip(),
                    'Each language phrase needs text')
            parts.append({'text':item['text'].strip(),'language':normalize_language(item.get('language',default))})
    require(sum(len(p['text']) for p in parts)+len(parts)-1<=5000,'Script must contain at most 5000 characters')
    return parts


def codec_token_budget(text,target_seconds=None):
    # CJK text cannot be budgeted by whitespace-separated word count alone.
    wide=sum(unicodedata.east_asian_width(c) in ['W','F'] and c.isalnum() for c in text)
    latin_words=len(re.findall(r'[^\W_]+', ''.join(' ' if unicodedata.east_asian_width(c) in ['W','F'] else c for c in text)))
    budget=min(1500,max(96,latin_words*7+wide*5+48))
    if target_seconds is not None:
        require(isinstance(target_seconds,(int,float)) and math.isfinite(target_seconds) and 3<=target_seconds<=600,
                'Invalid target duration')
        budget=min(budget,math.ceil((target_seconds*1.08+1)*12))
    return budget


def script_comparison(expected,actual,language):
    language=normalize_language(language)
    # ASR distance is a script-completeness signal, never a phonetic quality score.
    characters=language in ['Chinese','Japanese'] or any('\u3400'<=c<='\u9fff' or '\u3040'<=c<='\u30ff' for c in expected)
    def tokens(text):
        text=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')
        return [c for c in text if c.isalnum()] if characters else re.findall(r'\w+',text)
    a,b=tokens(expected),tokens(actual)
    require(bool(a),'Script needs letters or numbers')
    require(len(a)<=5000 and len(b)<=8000,'Transcript too long')
    row=list(range(len(b)+1))
    for i,left in enumerate(a,1):
        new=[i]
        for j,right in enumerate(b,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(left!=right)))
        row=new
    return {'rate':row[-1]/len(a),'edits':row[-1],'expected_units':len(a),
            'unit':'character' if characters else 'word','language':language,
            'note':'ASR script comparison only; pronunciation, accent and speaker identity need listening review.'}


def retime_spans(spans,timing):
    """Map synthesis boundaries through the measured tempo and inserted silence."""
    if timing is None:return [dict(s) for s in spans]
    def position(t):
        x=t/timing['tempo_factor']
        return timing['lead_seconds']+x+sum(p['seconds'] for p in timing.get('pause_insertions',[]) if p['at_seconds']<=x)
    return [{**s,'start':position(s['start']),'end':position(s['end'])} for s in spans]
