import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import CoursesPage from './pages/CoursesPage'
import QuizPage from './pages/QuizPage'
import VideoFeedPage from './pages/VideoFeedPage'
import ProfilePage from './pages/ProfilePage'
import { UploadProvider } from './contexts/UploadContext'
import { QuizSelectionProvider } from './contexts/QuizSelectionContext'
import { RatingProvider } from './contexts/RatingContext'

function App() {
  return (
    <RatingProvider>
      <UploadProvider>
        <QuizSelectionProvider>
          <BrowserRouter>
            <Layout>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/courses" element={<CoursesPage />} />
                <Route path="/quiz" element={<QuizPage />} />
                <Route path="/videos" element={<VideoFeedPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Routes>
            </Layout>
          </BrowserRouter>
        </QuizSelectionProvider>
      </UploadProvider>
    </RatingProvider>
  )
}

export default App


