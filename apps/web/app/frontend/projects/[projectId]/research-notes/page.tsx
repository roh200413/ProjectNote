'use client';

import { ChangeEvent, useEffect, useState } from 'react';

type ProjectFile = { token: string; label: string };

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('파일 읽기에 실패했습니다.'));
    reader.readAsDataURL(file);
  });
}

export default function ProjectResearchNotesPage({ params }: { params: { projectId: string } }) {
  const projectId = params.projectId;
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [summary, setSummary] = useState('');

  const [coverTitle, setCoverTitle] = useState('');
  const [coverCode, setCoverCode] = useState('');
  const [coverOrg, setCoverOrg] = useState('');
  const [coverManager, setCoverManager] = useState('');
  const [coverBusiness, setCoverBusiness] = useState('');
  const [coverAsset, setCoverAsset] = useState<File | null>(null);

  useEffect(() => {
    const run = async () => {
      setError('');
      const res = await fetch(`/api/projects/${projectId}/research-files`, { cache: 'no-store' });
      const body = (await res.json().catch(() => [])) as ProjectFile[] | { detail?: string };
      if (!res.ok) {
        setError((body as { detail?: string }).detail || '파일 목록 로드 실패');
        return;
      }
      setFiles(body as ProjectFile[]);
    };
    run();
  }, [projectId]);

  const selectedTokens = files.filter((f) => checked[f.token]).map((f) => f.token);

  const onMergeExport = () => {
    const params = new URLSearchParams();
    selectedTokens.forEach((token) => params.append('selected_file', token));
    window.open(`/api/projects/${projectId}/research-notes/export-pdf?${params.toString()}`, '_blank');
  };

  const onUpload = async () => {
    if (!uploadFile) {
      setMessage('업로드할 파일을 선택해주세요.');
      return;
    }
    const form = new FormData();
    form.set('research_note_file', uploadFile);
    form.set('title', title);
    form.set('author', author);
    form.set('summary', summary);

    const res = await fetch(`/api/projects/${projectId}/research-notes/upload`, { method: 'POST', body: form });
    const body = (await res.json().catch(() => ({}))) as { message?: string; detail?: string };
    setMessage(body.message || body.detail || (res.ok ? '업로드 완료' : '업로드 실패'));
  };

  const onSaveCover = async () => {
    const form = new FormData();
    form.set('title', coverTitle);
    form.set('code', coverCode);
    form.set('organization', coverOrg);
    form.set('manager', coverManager);
    form.set('business_name', coverBusiness);
    if (coverAsset) {
      const dataUrl = await fileToDataUrl(coverAsset);
      form.set('cover_image_data_url', dataUrl);
    }

    const res = await fetch(`/api/projects/${projectId}/cover`, { method: 'POST', body: form });
    const body = (await res.json().catch(() => ({}))) as { message?: string; detail?: string };
    setMessage(body.message || body.detail || (res.ok ? '표지 저장 완료' : '표지 저장 실패'));
  };

  const onCheck = (token: string, event: ChangeEvent<HTMLInputElement>) => {
    setChecked((prev) => ({ ...prev, [token]: event.target.checked }));
  };

  return (
    <main className="list-main">
      <section className="list-card">
        <span className="badge">고위험 이관 · 프로젝트 표지/병합/업로드</span>
        <h1>프로젝트 연구노트 작업</h1>

        {error && <p className="err">{error}</p>}
        {message && <p className="ok">{message}</p>}

        <h3>1) 파일 업로드</h3>
        <div className="toolbar" style={{ gridTemplateColumns: '1fr 1fr 1fr auto' }}>
          <input className="input" type="file" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
          <input className="input" placeholder="제목" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input className="input" placeholder="작성자" value={author} onChange={(e) => setAuthor(e.target.value)} />
          <button className="btn" onClick={onUpload}>업로드</button>
        </div>
        <textarea className="input" placeholder="요약" value={summary} onChange={(e) => setSummary(e.target.value)} rows={3} />

        <h3 style={{ marginTop: 20 }}>2) 표지 저장/출력</h3>
        <div className="toolbar" style={{ gridTemplateColumns: 'repeat(5, minmax(120px,1fr)) auto auto' }}>
          <input className="input" placeholder="표지 제목" value={coverTitle} onChange={(e) => setCoverTitle(e.target.value)} />
          <input className="input" placeholder="과제 번호" value={coverCode} onChange={(e) => setCoverCode(e.target.value)} />
          <input className="input" placeholder="기관" value={coverOrg} onChange={(e) => setCoverOrg(e.target.value)} />
          <input className="input" placeholder="작업자" value={coverManager} onChange={(e) => setCoverManager(e.target.value)} />
          <input className="input" placeholder="사업명" value={coverBusiness} onChange={(e) => setCoverBusiness(e.target.value)} />
          <input className="input" type="file" accept="image/*,application/pdf" onChange={(e) => setCoverAsset(e.target.files?.[0] || null)} />
          <button className="btn" onClick={onSaveCover}>표지 저장</button>
        </div>
        <div style={{ marginTop: 8 }}>
          <a className="btn-link" href={`/api/projects/${projectId}/cover/print`} target="_blank">표지 PDF 출력</a>
        </div>

        <h3 style={{ marginTop: 20 }}>3) 연구노트 병합 출력</h3>
        <table className="table">
          <thead><tr><th>선택</th><th>연구파일</th></tr></thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.token}>
                <td><input type="checkbox" checked={!!checked[f.token]} onChange={(e) => onCheck(f.token, e)} /></td>
                <td>{f.label}</td>
              </tr>
            ))}
            {!files.length && <tr><td colSpan={2} className="muted">연구파일이 없습니다.</td></tr>}
          </tbody>
        </table>
        <div className="pager" style={{ justifyContent: 'flex-start' }}>
          <button className="btn" onClick={onMergeExport} disabled={selectedTokens.length === 0}>선택 항목 병합 PDF</button>
          <a className="btn-link" href={`/api/projects/${projectId}/research-notes/export-pdf`} target="_blank">전체 병합 PDF</a>
        </div>
      </section>
    </main>
  );
}
