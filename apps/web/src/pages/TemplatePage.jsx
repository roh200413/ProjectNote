import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

function mockRows(title) {
  if (title.includes('로그인')) {
    return null;
  }

  return [
    { name: '암 전임상 연구', status: 'active', owner: '딥아이' },
    { name: 'AI 모델 검증', status: 'draft', owner: '연구소' }
  ];
}

export default function TemplatePage({ title, source }) {
  const params = useParams();
  const rows = useMemo(() => mockRows(title), [title]);

  return (
    <section className="card">
      <div className="badge">Converted from {source}</div>
      <h2>{title}</h2>
      {Object.keys(params).length > 0 && (
        <p className="meta">라우트 파라미터: {JSON.stringify(params)}</p>
      )}

      {title.includes('로그인') ? (
        <form className="stack">
          <input placeholder="이메일" type="email" />
          <input placeholder="비밀번호" type="password" />
          <button type="button">로그인</button>
        </form>
      ) : (
        <>
          <p className="meta">기존 HTML 화면을 React 라우트 기반 페이지로 이동한 기본 템플릿입니다.</p>
          {rows && (
            <table>
              <thead>
                <tr>
                  <th>이름</th>
                  <th>상태</th>
                  <th>기관</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.name}>
                    <td>{row.name}</td>
                    <td>{row.status}</td>
                    <td>{row.owner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
