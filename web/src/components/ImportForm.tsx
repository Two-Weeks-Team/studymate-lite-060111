import { useState, ChangeEvent, FormEvent } from 'react';

type ImportFormProps = {
  onGenerate: (text: string) => Promise<void>;
  loading: boolean;
};

export default function ImportForm({ onGenerate, loading }: ImportFormProps) {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    let content = text.trim();
    if (!content && file) {
      content = await file.text();
    }
    if (!content) {
      alert('Please provide some text or upload a .txt/.md file');
      return;
    }
    await onGenerate(content);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <textarea
        placeholder="Paste your notes here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={8}
        className="p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      ></textarea>
      <div className="flex items-center gap-2">
        <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Upload .txt/.md
          <input type="file" accept=".txt,.md" className="hidden" onChange={handleFileChange} />
        </label>
        {file && <span className="text-sm">{file.name}</span>}
      </div>
      <button
        type="submit"
        disabled={loading}
        className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? 'Generating...' : 'Generate Flashcards'}
      </button>
    </form>
  );
}
