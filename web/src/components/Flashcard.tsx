type FlashcardProps = {
  data: {
    id: string;
    question: string;
    answer: string;
    next_review: string;
  };
  onAnswer: (correct: boolean) => void;
};

export default function Flashcard({ data, onAnswer }: FlashcardProps) {
  return (
    <div className="border rounded-lg p-4 shadow-md bg-white">
      <h2 className="text-xl font-semibold mb-2">Q: {data.question}</h2>
      <p className="mb-4">A: {data.answer}</p>
      <div className="flex justify-between">
        <button
          onClick={() => onAnswer(true)}
          className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700"
        >
          Correct
        </button>
        <button
          onClick={() => onAnswer(false)}
          className="bg-red-600 text-white px-3 py-1 rounded-md hover:bg-red-700"
        >
          Incorrect
        </button>
      </div>
    </div>
  );
}
