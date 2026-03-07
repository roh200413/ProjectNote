import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import TemplatePage from './pages/TemplatePage';
import { routeCatalog } from './pages/routeCatalog';

export default function App() {
  return (
    <AppLayout>
      <Routes>
        {routeCatalog.map((item) => (
          <Route
            key={item.path}
            path={item.path}
            element={<TemplatePage source={item.source} title={item.title} />}
          />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
