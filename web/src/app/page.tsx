'use client';
import { useState } from 'react';
import ImportForm from '@/components/ImportForm';
import Flashcard from '@/components/Flashcard';
import { generateFlashcards, submitReview } from '@/lib/api';

type FlashcardData = {
  id: string;
  question: string;
  answer: string;
  next_review: string;
};

export default function HomePage() {
  const [flashcards, setFlashcards] = useState<FlashcardData[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (text: string) => {
    setLoading(true);
    try {
      const cards = await generateFlashcards(text, 10);
      setFlashcards(cards);
      setCurrentIndex(0);
    } catch (e) {
      console.error(e);
      alert('Failed to generate flashcards');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (cardId: string, correct: boolean) => {
    try {
      await submitReview(cardId, correct);
      // move to next card
      if (currentIndex < flashcards.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        alert('Deck completed!');
        setFlashcards([]);
        setCurrentIndex(0);
      }
    } catch (e) {
      console.error(e);
      alert('Failed to submit review');
    }
  };

  return (
    <main className="w-full max-w-2xl">
      <h1 className="text-3xl font-bold text-center mb-6">StudyMate Lite</h1>
      {flashcards.length === 0 ? (
        <ImportForm onGenerate={handleGenerate} loading={loading} />
      ) : (
        <Flashcard
          data={flashcards[currentIndex]}
          onAnswer={(correct) => handleReview(flashcards[currentIndex].id, correct)}
        />
      )}
    </main>
  );
}
