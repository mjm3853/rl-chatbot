import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Agents } from './pages/Agents';
import { Chat } from './pages/Chat';
import { Conversations } from './pages/Conversations';
import { TestCases } from './pages/TestCases';
import { Evaluations } from './pages/Evaluations';
import { Training } from './pages/Training';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="agents" element={<Agents />} />
        <Route path="chat" element={<Chat />} />
        <Route path="conversations" element={<Conversations />} />
        <Route path="test-cases" element={<TestCases />} />
        <Route path="evaluations" element={<Evaluations />} />
        <Route path="training" element={<Training />} />
      </Route>
    </Routes>
  );
}

export default App;
