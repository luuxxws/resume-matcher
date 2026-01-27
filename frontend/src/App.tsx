import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { Match } from './components/Match';
import { ResumeList } from './components/ResumeList';
import { Import } from './components/Import';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/match" element={<Match />} />
        <Route path="/resumes" element={<ResumeList />} />
        <Route path="/import" element={<Import />} />
      </Routes>
    </Layout>
  );
}
