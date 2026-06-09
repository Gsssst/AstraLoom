export type MetadataFieldKey =
  | 'title'
  | 'authors'
  | 'year'
  | 'abstract'
  | 'identifier'
  | 'pdf'
  | 'full_text'
  | 'embedding'
  | 'tags'
  | 'citation_count';

export interface ResearchPaperLike {
  id?: string | null;
  title?: string | null;
  authors?: string[] | string | null;
  year?: number | string | null;
  abstract?: string | null;
  abstract_full?: string | null;
  doi?: string | null;
  arxiv_id?: string | null;
  pdf_url?: string | null;
  has_pdf?: boolean;
  full_text_preview?: string | null;
  has_full_text?: boolean;
  has_embedding?: boolean;
  has_tags?: boolean;
  tags?: unknown;
  citation_count?: number | null;
}

export interface MetadataQualityCheck {
  key: MetadataFieldKey;
  label: string;
  ready: boolean;
  weight: number;
}

export interface MetadataQualityResult {
  checks: MetadataQualityCheck[];
  ready: number;
  total: number;
  readyWeight: number;
  totalWeight: number;
  percent: number;
  tier: 'ready' | 'usable' | 'weak';
}

export interface DuplicateRiskResult {
  key: string;
  count: number;
  risk: 'none' | 'possible' | 'strong';
}

export interface EvidenceReferenceLike {
  type?: string | null;
  source?: string | null;
  score?: number | null;
  page?: number | null;
  page_start?: number | null;
}

export interface EvidenceMetaLike {
  evidence_count?: number | null;
  evidence_coverage?: number | null;
  evidence_insufficient?: boolean | null;
}

export interface EvidenceConfidenceInput {
  references?: EvidenceReferenceLike[] | null;
  evidence?: EvidenceMetaLike | null;
}

export type EvidenceConfidenceStatus = 'strong' | 'partial' | 'weak';

export interface EvidenceConfidenceResult {
  references: EvidenceReferenceLike[];
  currentPaperRefs: EvidenceReferenceLike[];
  evidenceCount: number;
  coverage: number;
  sourceDiversity: number;
  weightedScore: number;
  status: EvidenceConfidenceStatus;
}

const STOPWORDS = new Set([
  'a', 'an', 'and', 'are', 'as', 'at', 'based', 'by', 'for', 'from', 'in', 'into',
  'of', 'on', 'or', 'the', 'to', 'towards', 'toward', 'using', 'via', 'with',
  'learning', 'model', 'models', 'method', 'methods', 'approach', 'study',
]);

const normalizeIdentifier = (value?: string | null) => String(value || '')
  .toLowerCase()
  .replace(/^https?:\/\/(dx\.)?doi\.org\//, '')
  .replace(/^doi:\s*/i, '')
  .replace(/^arxiv:\s*/i, '')
  .replace(/v\d+$/, '')
  .trim();

export const normalizeTitleKey = (title?: string | null) => String(title || '')
  .toLowerCase()
  .normalize('NFKD')
  .replace(/[^\p{Letter}\p{Number}\s]/gu, ' ')
  .replace(/\s+/g, ' ')
  .trim();

const authorLastName = (authors?: ResearchPaperLike['authors']) => {
  const first = Array.isArray(authors) ? authors[0] : String(authors || '').split(/,|;|\band\b/)[0];
  const cleaned = String(first || '').trim();
  if (!cleaned) return 'paper';
  return cleaned.split(/\s+/).slice(-1)[0].replace(/[^a-zA-Z0-9]/g, '') || 'paper';
};

const titleKeyword = (title?: string | null) => {
  const tokens = normalizeTitleKey(title)
    .split(/\s+/)
    .filter(token => token.length > 3 && !STOPWORDS.has(token));
  return tokens[0] || 'untitled';
};

export const buildResearchCitationKey = (paper: ResearchPaperLike, index = 0) => {
  const author = authorLastName(paper.authors);
  const year = paper.year || 'nd';
  const keyword = titleKeyword(paper.title);
  const identifier = normalizeIdentifier(paper.arxiv_id || paper.doi);
  const suffix = identifier ? identifier.replace(/[^a-z0-9]/g, '').slice(-4) : String(index + 1);
  return `${author}${year}${keyword}${suffix}`
    .replace(/[^a-zA-Z0-9_:-]/g, '')
    .slice(0, 48);
};

export const computeMetadataQuality = (
  paper: ResearchPaperLike,
  options: { detail?: boolean } = {},
): MetadataQualityResult => {
  const checks: MetadataQualityCheck[] = [
    { key: 'title', label: '标题', ready: !!paper.title, weight: 1 },
    { key: 'authors', label: '作者', ready: Array.isArray(paper.authors) ? paper.authors.length > 0 : !!paper.authors, weight: 1 },
    { key: 'year', label: '年份', ready: !!paper.year, weight: 1 },
    { key: 'abstract', label: '摘要', ready: !!(paper.abstract_full || paper.abstract), weight: 1 },
    { key: 'identifier', label: 'DOI/arXiv', ready: !!paper.doi || !!paper.arxiv_id, weight: 2 },
    { key: 'full_text', label: '全文', ready: !!paper.has_full_text || !!paper.full_text_preview, weight: 2 },
    { key: 'embedding', label: '向量', ready: !!paper.has_embedding, weight: options.detail ? 0 : 1 },
    { key: 'tags', label: '标签', ready: !!paper.has_tags || (Array.isArray(paper.tags) ? paper.tags.length > 0 : !!paper.tags), weight: 0.5 },
    { key: 'citation_count', label: '引用', ready: Number(paper.citation_count || 0) > 0, weight: 0.5 },
  ];
  if (options.detail) {
    checks.splice(6, 0, { key: 'pdf', label: 'PDF', ready: !!paper.pdf_url || !!paper.has_pdf || !!paper.arxiv_id, weight: 1 });
  }
  const totalWeight = checks.reduce((sum, check) => sum + check.weight, 0);
  const readyWeight = checks.reduce((sum, check) => sum + (check.ready ? check.weight : 0), 0);
  const percent = Math.round((readyWeight / totalWeight) * 100);
  return {
    checks,
    ready: checks.filter(check => check.ready).length,
    total: checks.length,
    readyWeight,
    totalWeight,
    percent,
    tier: percent >= 80 ? 'ready' : percent >= 55 ? 'usable' : 'weak',
  };
};

export const duplicateRiskKey = (paper: ResearchPaperLike) => {
  const doi = normalizeIdentifier(paper.doi);
  if (doi) return `doi:${doi}`;
  const arxiv = normalizeIdentifier(paper.arxiv_id);
  if (arxiv) return `arxiv:${arxiv}`;
  return `title:${normalizeTitleKey(paper.title)}`;
};

export const computeDuplicateRiskMap = (papers: ResearchPaperLike[]) => {
  const counts = papers.reduce<Record<string, number>>((acc, paper) => {
    const key = duplicateRiskKey(paper);
    if (key !== 'title:') acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  return counts;
};

export const duplicateRiskForPaper = (
  paper: ResearchPaperLike,
  duplicateMap: Record<string, number>,
): DuplicateRiskResult => {
  const key = duplicateRiskKey(paper);
  const count = duplicateMap[key] || 0;
  return {
    key,
    count,
    risk: count <= 1 ? 'none' : key.startsWith('title:') ? 'possible' : 'strong',
  };
};

export const computeEvidenceConfidence = (input: EvidenceConfidenceInput): EvidenceConfidenceResult => {
  const references = input.references || [];
  const currentPaperRefs = references.filter(ref => ref.type === 'paper_evidence' || ref.source === 'current_paper');
  const evidenceCount = input.evidence?.evidence_count ?? currentPaperRefs.length;
  const coverage = Math.max(0, Math.min(1, input.evidence?.evidence_coverage ?? Math.min(1, evidenceCount / 3)));
  const sourceDiversity = new Set(references.map(ref => ref.source || ref.type || 'unknown')).size;
  const avgCurrentScore = currentPaperRefs.length
    ? currentPaperRefs.reduce((sum, ref) => sum + Number(ref.score || 0.65), 0) / currentPaperRefs.length
    : 0;
  const weightedScore = Math.max(0, Math.min(1,
    coverage * 0.45
    + Math.min(evidenceCount, 4) / 4 * 0.25
    + Math.min(sourceDiversity, 3) / 3 * 0.1
    + avgCurrentScore * 0.2
    - (input.evidence?.evidence_insufficient ? 0.35 : 0),
  ));
  return {
    references,
    currentPaperRefs,
    evidenceCount,
    coverage,
    sourceDiversity,
    weightedScore,
    status: weightedScore >= 0.68 ? 'strong' : weightedScore >= 0.34 ? 'partial' : 'weak',
  };
};

export const scoreGraphEdgeStrength = (input: {
  relation?: string;
  score?: number | null;
  count?: number | null;
  category?: string | null;
}): 'strong' | 'medium' | 'weak' => {
  const relation = String(input.relation || '').toLowerCase();
  if (input.score != null) {
    if (input.score >= 0.75) return 'strong';
    if (input.score >= 0.4) return 'medium';
  }
  if ((input.count || 0) >= 3) return 'strong';
  if (['supports gap', 'proposal', 'contains', '摘录'].includes(relation)) return 'strong';
  if (['evidence', 'supports', 'related'].includes(relation) || input.category === 'seed') return 'medium';
  return 'weak';
};
