# PDF Viewer with Overlay Support

A custom PDF.js-based viewer with support for overlays, annotations, and interactive elements. Perfect for displaying tax forms (W-2, 1040) with contextual explanations and field highlights.

## Features

- ✅ **Self-hosted PDF.js** - No external dependencies or CORS issues
- ✅ **Text selection** - Full text layer for accessibility and copying
- ✅ **Zoom & navigation** - Zoom in/out, page navigation, fit-to-width
- ✅ **Annotation overlays** - Position tooltips, bubbles, and highlights on specific PDF coordinates
- ✅ **Coordinate mapping** - Automatic conversion from PDF coordinates to viewport coordinates
- ✅ **Responsive** - Handles zoom, scroll, and window resize

## Basic Usage

```tsx
import { PdfViewer } from '@/components/pdf-viewer';

function MyComponent() {
  return (
    <PdfViewer
      url="https://example.com/document.pdf"
      className="w-full h-screen"
    />
  );
}
```

## With Annotations

```tsx
import { PdfViewer, PdfAnnotation } from '@/components/pdf-viewer';
import { PdfAnnotationBubble } from '@/components/pdf-viewer/pdf-annotation-bubble';

function TaxFormViewer() {
  const annotations: PdfAnnotation[] = [
    {
      id: 'w2-box-1',
      page: 1, // Page number (1-indexed)
      bbox: {
        x: 100,    // X coordinate in PDF units (72 DPI, origin bottom-left)
        y: 500,    // Y coordinate
        w: 150,    // Width
        h: 30      // Height
      },
      content: (
        <PdfAnnotationBubble
          title="Wages Explanation"
          message="This is your total wages from W-2 Form, Box 1. This amount includes tips and other compensation."
          type="info"
          pinCite="From W-2 Acme Corp, Box 1"
        />
      )
    },
    {
      id: 'w2-box-2',
      page: 1,
      bbox: { x: 100, y: 450, w: 150, h: 30 },
      content: (
        <PdfAnnotationBubble
          title="Federal Withholding"
          message="Federal income tax withheld from your wages."
          type="success"
          pinCite="From W-2 Acme Corp, Box 2"
        />
      )
    }
  ];

  return (
    <PdfViewer
      url="https://example.com/w2-form.pdf"
      annotations={annotations}
      onPageChange={(page) => console.log('Page changed:', page)}
      className="w-full h-screen"
    />
  );
}
```

## Finding PDF Coordinates

### Method 1: From Textract/OCR Data

If you have Textract bounding boxes:

```typescript
// Textract gives you: { Left, Top, Width, Height } (0-1 normalized)
// Convert to PDF coordinates (72 DPI, assume 8.5x11" page)

const textractBox = {
  Left: 0.1,
  Top: 0.2,
  Width: 0.3,
  Height: 0.05
};

const pageWidth = 8.5 * 72;   // 612 points
const pageHeight = 11 * 72;    // 792 points

const pdfBbox = {
  x: textractBox.Left * pageWidth,
  y: (1 - textractBox.Top - textractBox.Height) * pageHeight, // Flip Y axis
  w: textractBox.Width * pageWidth,
  h: textractBox.Height * pageHeight
};
```

### Method 2: From AcroForm Fields

If you have fillable PDF forms:

```typescript
// Use pdf-lib to extract field positions
import { PDFDocument } from 'pdf-lib';

const pdfBytes = await fetch(url).then(res => res.arrayBuffer());
const pdfDoc = await PDFDocument.load(pdfBytes);
const form = pdfDoc.getForm();
const field = form.getTextField('taxpayer_name');
const widgets = field.acroField.getWidgets();

const rect = widgets[0].getRectangle();
// rect is already in PDF coordinates!
const bbox = {
  x: rect.x,
  y: rect.y,
  w: rect.width,
  h: rect.height
};
```

### Method 3: Manual Measurement

Use a PDF editor (Adobe Acrobat, PDF-XChange) with rulers enabled, or use the browser dev tools to inspect the rendered canvas and calculate coordinates.

## Annotation Types

The `PdfAnnotationBubble` component supports different visual styles:

```tsx
<PdfAnnotationBubble
  type="info"     // Blue (default)
  type="success"  // Green
  type="warning"  // Yellow
  type="help"     // Purple
/>
```

## Custom Annotations

You can pass any React component as annotation content:

```tsx
const annotations: PdfAnnotation[] = [
  {
    id: 'custom-1',
    page: 1,
    bbox: { x: 100, y: 500, w: 150, h: 30 },
    content: (
      <div className="bg-white border-2 border-red-500 rounded-lg p-4 shadow-xl">
        <h3 className="font-bold">Custom Annotation</h3>
        <p>Any React component works here!</p>
        <button onClick={() => alert('Clicked!')}>
          Learn More
        </button>
      </div>
    )
  }
];
```

## Advanced: Dynamic Annotations

Load annotations from your backend:

```tsx
function DynamicPdfViewer({ documentId }: { documentId: string }) {
  const [annotations, setAnnotations] = useState<PdfAnnotation[]>([]);

  useEffect(() => {
    async function loadAnnotations() {
      // Fetch from your API
      const response = await fetch(`/api/documents/${documentId}/annotations`);
      const data = await response.json();

      // Transform to PdfAnnotation format
      const pdfAnnotations = data.map((ann: any) => ({
        id: ann.id,
        page: ann.page,
        bbox: ann.bbox,
        content: (
          <PdfAnnotationBubble
            title={ann.title}
            message={ann.explanation}
            pinCite={ann.source}
            type={ann.type}
          />
        )
      }));

      setAnnotations(pdfAnnotations);
    }

    loadAnnotations();
  }, [documentId]);

  return (
    <PdfViewer
      url={`/api/documents/${documentId}/pdf`}
      annotations={annotations}
    />
  );
}
```

## Performance Tips

1. **Lazy load annotations** - Only create annotation content for the current page
2. **Memoize expensive renders** - Use `React.memo()` for annotation components
3. **Debounce zoom/scroll** - Avoid re-rendering annotations on every zoom level change
4. **Use virtualization** - For documents with hundreds of annotations

## Security Considerations

- **PII masking**: Never include SSNs or sensitive data in annotation text
- **Signed URLs**: Use short-lived S3 signed URLs for PDF access
- **CSP headers**: Ensure your Content-Security-Policy allows PDF.js worker
- **CORS**: Configure your S3 bucket to allow origin requests

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ⚠️ IE11 not supported (PDF.js requires modern JS)

## Troubleshooting

### "Worker not found" error

Make sure PDF.js worker is loading. The viewer uses CDN by default:

```tsx
// In pdf-viewer.tsx
pdfjsLib.GlobalWorkerOptions.workerSrc =
  `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
```

For self-hosting, download the worker and serve it locally:

```bash
cp node_modules/pdfjs-dist/build/pdf.worker.min.js public/
```

Then update the worker path:

```tsx
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
```

### Annotations not appearing

1. Check that `bbox` coordinates are in PDF coordinate space (origin bottom-left)
2. Verify the page number is correct (1-indexed)
3. Ensure the viewport is fully rendered before adding annotations
4. Check browser console for coordinate conversion errors

### Text layer not selectable

Make sure the text layer CSS is loaded:

```tsx
import '@/components/pdf-viewer/pdf-viewer.css';
```

## Examples

See `/src/app/test/pdf-viewer-demo` for a full working example with:
- Multiple annotation types
- Dynamic coordinate mapping
- W-2 form field highlights
- Explain Agent integration
