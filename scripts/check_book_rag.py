"""Opt-in acceptance against the user's private Razavi second-edition PDF."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.book import Book
from rag.config import Config

QUESTIONS = [
    ('2', '源体电压增大时，为什么阈值电压升高？', (43,44)),
    ('3', '源跟随器为什么输出电阻低，体效应怎样使电压增益小于一？', (87,92)),
    ('4', '尾电流源的有限输出电阻怎样改变差动对的共模响应？', (131,133)),
    ('5', '有源电流镜怎样把差分支路电流转换为单端输出？', (159,164)),
    ('6', '用米勒近似计算 Cgd 时，为什么不能把 Vout/Vin 当作栅漏之间的局部增益？', (188,191)),
    ('7', '两路不相关噪声为什么相加功率而不是直接相加幅度？', (227,227)),
    ('6', '当 Rs 很小时，栅节点 X 为什么近似交流固定？当 Rs 很大时，为什么漏端变化能够经 Cgd 影响 X，并产生等效 Rx？', (188,189)),
]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    book = Book(Config.load())
    results = []
    for chapter, query, expected in QUESTIONS:
        started = time.perf_counter()
        result = book.search(query, chapter=chapter)
        pages = [r['pdf_page'] for r in result['hits']]
        passed = any(expected[0] <= p <= expected[1] for p in pages)
        results.append({'chapter': chapter, 'query': query, 'expected_pdf_pages': expected,
                        'top5_pdf_pages': pages, 'hit': passed,
                        'seconds': round(time.perf_counter()-started,3), 'warnings': result['warnings']})
    exact = book.search('Fig. 6.14', chapter='6', mode='keyword')
    symbols = book.search('Rs CGD', chapter='6', mode='keyword')
    # Original English passages, not a claim to have tested an unavailable English PDF.
    documents = [
        'title: Source follower | text: A source follower buffers a high resistance voltage source. '
        'Its source follows the gate; body effect reduces its gain and adds output conductance.',
        'title: Current mirror | text: A diode connected reference transistor sets the gate voltage '
        'shared with an output transistor. Unequal drain voltages cause current copying error.',
        'title: Noise | text: Independent zero mean noise voltages have additive variances. '
        'Their power spectral densities add, but their amplitude spectral densities do not add directly.']
    queries = ['体效应为什么使源跟随增益降低', '镜像电流为何会受漏端电压影响', '独立噪声应该相加功率还是幅度']
    vectors = book.encoder.encode(documents)
    query_vectors = book.encoder.encode(queries,query=True)
    multilingual = (query_vectors @ vectors.T).argmax(axis=1).tolist()
    report = {'pdf_sha256': book.pdf_hash(), 'book_language': 'Chinese scanned edition',
              'metric':'chapter-filtered expected-page recall@5; inspect evidence and original images separately',
              'questions': results, 'hit_at_5': sum(r['hit'] for r in results), 'total': len(results),
              'exact_figure_top5': [r['pdf_page'] for r in exact['hits']],
              'symbol_top5': [r['pdf_page'] for r in symbols['hits']],
              'supplementary_chinese_to_original_english_passages': multilingual,
              'supplementary_expected': [0,1,2], 'device': book.encoder.status(),
              'status': book.status()}
    target = book.config.index.parent / 'acceptance.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # No book excerpts in the report: page references and independently written questions only.
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
