'use client';

import { useEffect, useMemo, useState } from 'react';

type Note = { id: string; title: string; summary?: string };
type FileRow = { id: string; name: string };

export default function ResearchNoteViewerPage({ params }: { params: { noteId: string } }) {
  const noteId = params.noteId;
  const [note, setNote] = useState<Note | null>(null);
  const [files, setFiles] = useState<FileRow[]>([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      setError('');
      try {
        const [noteRes, filesRes] = await Promise.all([
          fetch(`/api/research-notes`, { cache: 'no-store' }),
          fetch(`/api/research-notes/${noteId}/files`, { cache: 'no-store' }),
        ]);

        const noteList = (await noteRes.json().catch(() => [])) as Note[];
        const fileList = (await filesRes.json().catch(() => [])) as FileRow[];

        if (!noteRes.ok) throw new Error('연구노트 정보를 불러오지 못했습니다.');
        if (!filesRes.ok) throw new Error('파일 목록을 불러오지 못했습니다.');

        setNote((noteList || []).find((n) => n.id === noteId) || null);
        setFiles(fileList || []);
        if (fileList.length > 0) setSelectedFile(fileList[0].id);
      } catch (err) {
        setError(err instanceof Error ? err.message : '불러오기 실패');
      }
    };
    run();
  }, [noteId]);

  const selected = useMemo(() => files.find((f) => f.id === selectedFile), [files, selectedFile]);

  return (
    <main className="list-main">
      <section className="list-card">
        <span className="badge">고위험 이관 · 연구노트 viewer/print/export</span>
        <h1>{note?.title || '연구노트 파일 보기'}</h1>
        {error && <p className="err">{error}</p>}

        <div className="toolbar" style={{ gridTemplateColumns: '1fr auto auto auto' }}>
          <select className="input" value={selectedFile} onChange={(e) => setSelectedFile(e.target.value)}>
            {files.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
          <a className="btn-link" href={`/api/research-notes/${noteId}/files/${selectedFile}/content?download=1`}>
            파일 다운로드
          </a>
          <a className="btn-link" href={`/api/research-notes/${noteId}/export-pdf?file=${selectedFile}`}>
            PDF 내보내기
          </a>
          <a className="btn-link" href={`/frontend/research-notes/${noteId}`}>목록</a>
        </div>

        {!selectedFile && <p className="muted">표시할 파일이 없습니다.</p>}

        {selectedFile && (
          <section className="pn-preview">
            <div className="pn-preview-head">미리보기: {selected?.name}</div>
            {selected?.name.toLowerCase().endsWith('.pdf') ? (
              <iframe title="pdf preview" src={`/api/research-notes/${noteId}/files/${selectedFile}/content`} className="pn-frame" />
            ) : (
              <img src={`/api/research-notes/${noteId}/files/${selectedFile}/content`} alt={selected?.name} className="pn-image" />
            )}
          </section>
        )}
      </section>
    </main>
  );
}
