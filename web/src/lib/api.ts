export type FlashcardResponse = {
  id: string;
  question: string;
  answer: string;
  next_review: string;
};

/**
 * Call the backend generate endpoint.
 * @param text Raw notes/text.
 * @param maxCards Maximum number of cards to generate.
 */
export async function generateFlashcards(
  text: string,
  maxCards: number = 10
): Promise<FlashcardResponse[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, max_cards: maxCards }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err?.error?.message || 'Generation failed');
  }
  const data = await res.json();
  return data.cards as FlashcardResponse[];
}

/**
 * Submit a review result for a single flashcard.
 * @param cardId Identifier of the flashcard.
 * @param correct Whether the user answered correctly.
 */
export async function submitReview(
  cardId: string,
  correct: boolean
): Promise<void> {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/study/${cardId}/review`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ response: correct ? 'Correct' : 'Incorrect' }),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err?.error?.message || 'Review submission failed');
  }
}
