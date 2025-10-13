# Quick Start: Adding W-2 Annotations

## 30-Second Integration

### 1. Basic PDF Display
```tsx
import { PdfViewer } from '@/components/pdf-viewer';

<PdfViewer url="https://your-bucket.s3.amazonaws.com/w2.pdf" />
```

### 2. With Annotations
```tsx
import { PdfViewer, PdfAnnotation, PdfAnnotationBubble } from '@/components/pdf-viewer';

const w2Annotations: PdfAnnotation[] = [
  {
    id: 'wages',
    page: 1,
    bbox: { x: 100, y: 500, w: 150, h: 30 }, // PDF coordinates
    content: (
      <PdfAnnotationBubble
        title="Total Wages"
        message="From W-2 Box 1: Wages, tips, other compensation"
        type="info"
        pinCite="Form W-2, Acme Corp"
      />
    )
  }
];

<PdfViewer url={w2Url} annotations={w2Annotations} />
```

## Coordinate Conversion Cheat Sheet

### From Textract (normalized 0-1)
```typescript
const bbox = {
  x: textract.Left * 612,
  y: (1 - textract.Top - textract.Height) * 792,
  w: textract.Width * 612,
  h: textract.Height * 792
};
```

### From Pixels (assuming 96 DPI screen)
```typescript
const bbox = {
  x: pixelX * (72/96),
  y: (pageHeight - pixelY - pixelHeight) * (72/96),
  w: pixelWidth * (72/96),
  h: pixelHeight * (72/96)
};
```

## Bubble Types

| Type | Color | Use Case |
|------|-------|----------|
| `info` | Blue | Explanations, definitions |
| `success` | Green | Validated/verified data |
| `warning` | Yellow | Potential issues, review needed |
| `help` | Purple | Tips, recommendations |

## Common W-2 Boxes (Approximate Coordinates)

```typescript
// Standard W-2 form coordinates (may vary by template)
const W2_FIELDS = {
  box1: { x: 95, y: 585, w: 140, h: 18 },   // Wages
  box2: { x: 95, y: 560, w: 140, h: 18 },   // Federal tax
  box3: { x: 265, y: 585, w: 140, h: 18 },  // SS wages
  box4: { x: 265, y: 560, w: 140, h: 18 },  // SS tax
  box5: { x: 435, y: 585, w: 140, h: 18 },  // Medicare wages
  box6: { x: 435, y: 560, w: 140, h: 18 },  // Medicare tax
};
```

## Integration with Your Explain Agent

```typescript
function W2ViewerWithExplanations({ documentId }: { documentId: string }) {
  const [annotations, setAnnotations] = useState<PdfAnnotation[]>([]);
  const [pdfUrl, setPdfUrl] = useState('');

  useEffect(() => {
    // Fetch document and explanations
    async function load() {
      const doc = await fetch(`/api/documents/${documentId}`);
      const data = await doc.json();
      setPdfUrl(data.url);

      // Get AI explanations
      const explanations = await fetch(`/api/agents/explain-w2/${documentId}`);
      const exp = await explanations.json();

      // Convert to annotations
      const annos = exp.fields.map((field: any) => ({
        id: field.id,
        page: 1,
        bbox: field.bbox,
        content: (
          <PdfAnnotationBubble
            title={field.label}
            message={field.explanation}
            type={field.validated ? 'success' : 'info'}
            pinCite={field.source}
          />
        )
      }));

      setAnnotations(annos);
    }

    load();
  }, [documentId]);

  return <PdfViewer url={pdfUrl} annotations={annotations} />;
}
```

## Testing Locally

1. **Open the app**: http://localhost:3001/app
2. **Click on a W-2 document** in the explorer panel
3. **PDF should load** in the main editor with zoom controls
4. **Add test annotations** by modifying the mock data

## Server Status

Your dev server is running on: **http://localhost:3001**

The PDF viewer is now fully integrated and ready to use! 🎉
