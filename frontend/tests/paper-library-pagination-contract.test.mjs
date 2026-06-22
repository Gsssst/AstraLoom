import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const papersPageSource = readFileSync(
  new URL('../src/pages/PapersPage.tsx', import.meta.url),
  'utf8',
);

test('paper library stores search total and displays API total instead of loaded page length', () => {
  assert.match(papersPageSource, /const \[searchTotal, setSearchTotal\] = useState\(0\)/);
  assert.match(papersPageSource, /setSearchTotal\(Number\(r\.data\.total \|\| 0\)\)/);
  assert.match(papersPageSource, /const statsTotal = isSearchBackedSource \? searchTotal : papers\.length/);
  assert.match(papersPageSource, /const stats = statsTotal > 0 \? `共 \$\{statsTotal\} 篇论文` : ''/);
  assert.doesNotMatch(papersPageSource, /const stats = papers\.length > 0 \? `共 \$\{papers\.length\} 篇论文` : ''/);
});

test('paper library sends requested page to local and remote search-backed views', () => {
  assert.match(papersPageSource, /const \[searchPage, setSearchPage\] = useState\(1\)/);
  assert.match(papersPageSource, /const \[searchPageSize, setSearchPageSize\] = useState\(PAPER_SEARCH_PAGE_SIZE\)/);
  assert.match(papersPageSource, /const handleSearch = useCallback\(async \(requestedPage = 1\) =>/);
  assert.match(papersPageSource, /page: requestedPage/);
  assert.match(papersPageSource, /page_size: searchPageSize/);
  assert.doesNotMatch(papersPageSource, /const requestedPage = isRemoteSource \? requestedRemotePage : 1/);
});

test('paper library renders pagination controls for search-backed results', () => {
  assert.match(papersPageSource, /Pagination,/);
  assert.match(papersPageSource, /const showSearchPagination = isSearchBackedSource/);
  assert.match(papersPageSource, /<Pagination/);
  assert.match(papersPageSource, /current=\{searchPage\}/);
  assert.match(papersPageSource, /total=\{searchPaginationTotal\}/);
  assert.match(papersPageSource, /onChange=\{page => handleSearch\(page\)\}/);
  assert.match(papersPageSource, /第 \$\{range\[0\]\}-\$\{range\[1\]\} 篇，共 \$\{total\} 篇/);
});

test('paper library resets search-backed pagination when search context changes', () => {
  assert.match(papersPageSource, /setSearchPage\(1\)/);
  assert.match(papersPageSource, /setSearchTotal\(0\)/);
  assert.match(papersPageSource, /useEffect\(\(\) => \{ handleSearch\(1\); \}, \[source, sort, readingStatus, selectedCollectionId, urlSearchRevision, filterImporter, filterLocalSource, filterFullText, filterEmbedding, filterReadStatus, filterImportance\]\)/);
  assert.match(papersPageSource, /onSearch=\{\(\) => handleSearch\(1\)\}/);
});
