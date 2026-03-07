import LegacyIframePage from '../_components/LegacyIframePage';

export default function CatchAllLegacyFrontendPage({ params }: { params: { legacy?: string[] } }) {
  const path = (params.legacy || []).join('/');
  return <LegacyIframePage path={path} />;
}
