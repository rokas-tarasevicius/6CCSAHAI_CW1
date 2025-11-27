import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import CoursesPage from './pages/CoursesPage'
import QuizPage from './pages/QuizPage'
import VideoFeedPage from './pages/VideoFeedPage'
import { UploadProvider } from './contexts/UploadContext'
import { QuizSelectionProvider } from './contexts/QuizSelectionContext'

function App() {
  return (
    <UploadProvider>
      <QuizSelectionProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/courses" element={<CoursesPage />} />
              <Route path="/quiz" element={<QuizPage />} />
              <Route path="/videos" element={<VideoFeedPage />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </QuizSelectionProvider>
    </UploadProvider>
  )
}

export default App


