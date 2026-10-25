"""MinerU worker: run only with the separate uv OCR interpreter."""
import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from rag.config import RagError, sha256


def configure(home):
    home.mkdir(parents=True,exist_ok=True)
    settings = home/'techcodex-ocr.yaml'
    settings.write_text(json.dumps({'model':{'base_dir':str(home/'models'),'source':'local',
        'small_backend':'onnx','vlm':{'engine':'llama-cpp','server_url':''}},
        'llm_aided':{'features':{'title_leveling':False,'cross_page_table_cell_merge':False}}}),encoding='utf-8')
    os.environ.update(MINERU_HOME=str(home),MINERU_CONFIG=str(settings),MINERU_MODEL_SOURCE='local',
        MINERU_MODEL_SMALL_BACKEND='onnx',MINERU_TABLE_DEVICE='cpu',CUDA_VISIBLE_DEVICES='-1',
        MINERU_LLAMA_CPP_BACKEND='cpu',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MINERU_INTRA_OP_NUM_THREADS='4',MINERU_INTER_OP_NUM_THREADS='1')


def model_manifest(home):
    from mineru.model.registry import MINERU_4_MODELS_ONNX
    from mineru.model.download import verify_model_repo
    readiness = verify_model_repo(MINERU_4_MODELS_ONNX)
    if not readiness.ready:
        raise RagError('MinerU Basic ONNX assets missing; explicitly run mineru-kit models download --tier basic --small-backend onnx')
    files = {name:sha256(home/'models'/MINERU_4_MODELS_ONNX.name/name)
             for name in sorted(set(MINERU_4_MODELS_ONNX.paths.values()))}
    source = home/'model-source.json'
    revision = None
    if source.is_file():
        record = json.loads(source.read_text(encoding='utf-8'))
        revision = record.get('sha')
        for item in record.get('siblings',[]):
            name = item['rfilename']
            if name in files and item.get('lfs',{}).get('sha256') and files[name] != item['lfs']['sha256']:
                raise RagError(f'OCR model checksum differs from official pinned source: {name}')
    fingerprint = hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    return {'engine':'MinerU','version':importlib.metadata.version('mineru'),
            'docvortex':importlib.metadata.version('docvortex'),'small_backend':'onnx',
            'device':'cpu','model_repo':'opendatalab/MinerU-4_models_onnx',
            'model_revision':revision,'model_fingerprint':fingerprint,'files_sha256':files}


def formulas(blocks, parent_bbox=None):
    found = []
    for block in blocks:
        if not isinstance(block,dict):
            continue
        bbox = block.get('bbox') or parent_bbox
        if block.get('type') in ('equation','equation_inline'):
            found.append({'latex_raw':block.get('content',''),'bbox':bbox,
                          'confidence':None,'needs_review':True,
                          'reason':'Formula transcription is not a calibrated confidence estimate; verify original page'})
        for value in block.values():
            if isinstance(value,list):
                found.extend(formulas(value,bbox))
    return found


def text_scores(value):
    """Use OCR text scores only, never layout/detection scores as formula accuracy."""
    scores = []
    if isinstance(value,dict):
        if value.get('type') == 'text' and isinstance(value.get('score'),(int,float)):
            scores.append(float(value['score']))
        for item in value.values():
            scores.extend(text_scores(item))
    elif isinstance(value,list):
        for item in value:
            scores.extend(text_scores(item))
    return scores


def parse_pages(args):
    import pymupdf
    import onnxruntime
    from mineru.parser import parse, ParseResult
    from mineru.parser.writer import FileBasedDataWriter
    from rag.book import page_info
    from rag.pdf import text_layer_quality
    requested = sorted(set(int(p) for p in args.pages.split(',')))
    limit = 20 if args.tier == 'basic' else 3
    if not requested or len(requested) > limit or (args.tier != 'basic' and not args.reason.strip()):
        raise RagError('Select a bounded page batch; higher tiers require an explicit review reason')
    source_hash = sha256(args.pdf)
    provenance = {**model_manifest(args.home),'tier':args.tier,'reason':args.reason,
                  'onnxruntime':onnxruntime.__version__,'vlm_loaded':args.tier != 'basic'}
    if args.tier != 'basic':
        from mineru.model.registry import MINERU_2_5_PRO_2605_1_2B_GGUF
        repo = MINERU_2_5_PRO_2605_1_2B_GGUF
        vlm_files = {p:sha256(repo.local_dir()/p) for p in repo.paths.values()}
        provenance['vlm'] = {'repo':repo.repos['huggingface'],'files_sha256':vlm_files,'backend':'llama.cpp CPU',
                             'engine_version':importlib.metadata.version('mineru-llama-cpp')}
        source = args.home/'vlm-source.json'
        if source.is_file():
            metadata = json.loads(source.read_text(encoding='utf-8'))
            for file in metadata.get('siblings',[]):
                name = file['rfilename']
                if name in vlm_files and file.get('lfs',{}).get('sha256') != vlm_files[name]:
                    raise RagError(f'VLM weight checksum mismatch: {name}')
            provenance['vlm']['revision'] = metadata.get('sha')
    with pymupdf.open(args.pdf) as doc:
        if requested[0] < 1 or requested[-1] > len(doc):
            raise RagError('Requested OCR page outside the original PDF')
        selected = [p for p in requested if not text_layer_quality(doc[p-1])['reliable']]
        if not selected:
            return {'ocr_pages':0,'reason':'all selected pages have reliable native text'}
        # Statless SDK: no doclib service, public port, implicit all-pages parse or query-time OCR.
        result = parse(args.pdf,tier=args.tier,ocr_mode='ocr',page_range=','.join(map(str,selected)))
        middle = result.to_dict()
        returned = {p['page_idx']+1 for p in middle['pages']}
        if returned != set(selected):
            raise RagError(f'MinerU original-page mapping mismatch: expected {selected}, got {sorted(returned)}')
        output = args.output
        run_dir = output/'runs'/('-'.join(map(str,selected)))
        result.save(FileBasedDataWriter(str(run_dir)))
        model_output = json.loads((run_dir/'model_output.json').read_text(encoding='utf-8'))
        model_pages = dict(zip(model_output['page_index_map'],model_output['pages']))
        summary = []
        for page in middle['pages']:
            number = page['page_idx']+1
            blocks = []
            for block in page['blocks']:
                single = {**middle,'pages':[{'page_idx':page['page_idx'],'blocks':[block]}]}
                text = ParseResult.from_dict(single).markdown()
                blocks.append({'type':block['type'],'index':block.get('index'),'bbox':block.get('bbox'),
                               'text':text,'raw':block})
            equations = formulas(page['blocks'])
            scores = text_scores(model_pages.get(page['page_idx'],[]))
            flags = []
            if equations:
                flags.append('formula transcription needs original-image verification')
            if any(s < .8 for s in scores):
                flags.append('low-confidence OCR text spans; inspect model_output.json and original image')
            if any(not f['latex_raw'].strip() or f['latex_raw'].count('{') != f['latex_raw'].count('}') for f in equations):
                flags.append('missing or unbalanced formula; consider selected-page higher-tier parsing')
            import re
            if any(re.fullmatch(r'\s*[（(]\d+\.\d+[）)]\s*',b['text']) for b in blocks if b['type']=='text'):
                flags.append('isolated equation number may indicate an omitted formula')
            record = {'schema':'techcodex.ocr.v2','pdf_sha256':source_hash,'pdf_page':number,
                      **page_info(doc,number),'text_layer':text_layer_quality(doc[number-1]),
                      'provenance':provenance,'blocks':blocks,'formulas':equations,
                      'text_confidence':sum(scores)/len(scores) if scores else None,
                      'confidence_kind':'OCR text spans only' if scores else 'not provided by parser',
                      'review_flags':flags,'review_status':'pending','raw_artifacts':str(run_dir.relative_to(output))}
            record['figure_refs'] = [{'label':m.group(0),'block_index':b['index'],'bbox':b['bbox']}
                                     for b in blocks for m in re.finditer(r'(?:图|Fig\.?|Figure)\s*\d+\.\d+',b['text'],re.I)]
            output.mkdir(parents=True,exist_ok=True)
            target = output/f'{number}.json'
            temporary = target.with_suffix('.tmp')
            temporary.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            temporary.replace(target)
            summary.append({'pdf_page':number,'printed_label':record['printed_label'],
                            'blocks':len(blocks),'formulas':len(equations),'review_flags':flags})
    return {'ocr_pages':len(summary),'pages':summary,'provenance':provenance}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['verify','parse'])
    parser.add_argument('--home',type=Path,default=ROOT/'.local/mineru')
    parser.add_argument('--pdf',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--pages',default='')
    parser.add_argument('--tier',choices=['basic','standard','advanced'],default='basic')
    parser.add_argument('--reason',default='')
    args = parser.parse_args()
    args.home = args.home.resolve()
    configure(args.home)
    with contextlib.redirect_stdout(sys.stderr):
        report = model_manifest(args.home) if args.command == 'verify' else parse_pages(args)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
