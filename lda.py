"""LDA riêng theo ngôn ngữ và chọn k theo UMass trên ma trận nhị phân."""
from lam_sach import lam_sach
from tu_dien import E5

STOP_VI = set('và của là các những trong cho với được có một về theo đã này đó từ đến tại để cũng như trên công ty doanh nghiệp'.split())

def tach_vi(text):
    try:
        from underthesea import word_tokenize
    except ImportError:
        words = text.split()
        return ['_'.join(words[i:i+2]) for i in range(len(words)-1)
                if all(w not in STOP_VI for w in words[i:i+2])]
    return [w.replace(' ', '_') for w in word_tokenize(text)
            if w not in STOP_VI and len(w) > 1]

def nhan_topic(words):
    import re
    normalized = [w.replace('_', ' ') for w in words]
    has_e5 = any(re.fullmatch(pattern, w) or w in vi
                 for _, pattern, vi in E5 for w in normalized)
    operating = {'waste','material','materials','recycling','recycled','treatment','energy','water','tons',
                 'chất thải','nguyên liệu','vật liệu','tái chế','xử lý','năng lượng','nước','tấn','thu hồi'}
    symbolic = {'governance','management','stakeholders','sustainable','policy','development',
                'quản trị','quản lý','bền vững','chính sách','phát triển','bên liên quan'}
    if has_e5 and any(w in operating for w in normalized):
        return 'Substantive E5'
    if sum(w in symbolic for w in normalized) >= 2:
        return 'Symbolic'
    return 'Ngoài E5'

def chay_lda(reports):
    import numpy as np
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    result = {'ghi_chu': 'Nhãn chủ đề là gợi ý tự động, cần người kiểm tra lại. Tỷ trọng là trung bình theo trang.', 'nhom': {}}
    for language in ('vi', 'en'):
        docs, owners = [], []
        for report in reports:
            if report['ngon_ngu'] != language:
                continue
            for page in report['pages']:
                clean = lam_sach(page['text'])
                if len(clean.split()) >= 40:
                    docs.append(clean)
                    owners.append(report['id'])
        group = {'so_van_ban': len(docs), 'trang_thai': '', 'thu_k': [], 'chu_de': [], 'ty_trong_bao_cao': {}}
        result['nhom'][language] = group
        if len(docs) < 6:
            group['trang_thai'] = 'Bỏ qua: dưới 6 trang đủ 40 từ; min_df=3, max_df=0.5 không đủ dữ liệu.'
            continue
        kwargs = {'stop_words': 'english'} if language == 'en' else {'tokenizer': tach_vi, 'token_pattern': None, 'lowercase': False}
        vectorizer = CountVectorizer(min_df=3, max_df=0.5, **kwargs)
        try:
            matrix = vectorizer.fit_transform(docs)
        except ValueError as exc:
            group['trang_thai'] = f'Bỏ qua: {exc}'
            continue
        if matrix.shape[1] < 10:
            group['trang_thai'] = 'Bỏ qua: dưới 10 thuật ngữ sau lọc; không thể tính UMass trên 10 từ.'
            continue
        features = vectorizer.get_feature_names_out()
        binary = (matrix > 0).astype('int64').tocsc()
        def coherence(model):
            scores = []
            for component in model.components_:
                top = component.argsort()[-10:][::-1]
                for m in range(1, len(top)):
                    for n in range(m):
                        both = binary[:, top[m]].multiply(binary[:, top[n]]).sum()
                        scores.append(np.log((float(both)+1) / float(binary[:, top[n]].sum())))
            return float(np.mean(scores))
        best, best_score = None, float('-inf')
        for k in range(4, 13):
            model = LatentDirichletAllocation(n_components=k, random_state=42)
            model.fit(matrix)
            score = coherence(model)
            group['thu_k'].append({'k': k, 'umass': score})
            if score > best_score:
                best, best_score = model, score
        proportions = best.transform(matrix)
        group.update(k=best.n_components, umass=best_score, trang_thai='OK')
        for i, component in enumerate(best.components_):
            words = features[component.argsort()[-12:][::-1]].tolist()
            group['chu_de'].append({'chu_de': i+1, 'ty_trong': float(proportions[:, i].mean()),
                                    'tu_khoa': words, 'nhan': nhan_topic(words), 'can_kiem_tra': True})
        for owner in sorted(set(owners)):
            indices = [i for i, value in enumerate(owners) if value == owner]
            group['ty_trong_bao_cao'][owner] = proportions[indices].mean(axis=0).tolist()
    return result
