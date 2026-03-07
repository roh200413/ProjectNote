import { Navigate, Route, Routes } from 'react-router-dom';
import LegacyTemplatePage from './pages/LegacyTemplatePage';
import { routeCatalog } from './pages/routeCatalog';

export default function App() {
  return (
    <Routes>
      {routeCatalog.map((item) => (
        <Route key={item.path} element={<LegacyTemplatePage backendPath={item.backendPath} />} path={item.path} />
      ))}
      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
