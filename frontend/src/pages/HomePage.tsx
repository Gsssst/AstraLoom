import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Typography, Space, Row, Col, Tag } from 'antd';
import {
  CommentOutlined, BookOutlined, ExperimentOutlined, EditOutlined,
  SearchOutlined, ThunderboltOutlined, GlobalOutlined, RocketOutlined,
  ArrowRightOutlined, StarFilled, FireOutlined, BulbOutlined,
  ClockCircleOutlined, TeamOutlined,
} from '@ant-design/icons';
import '../styles/home.css';

const { Text } = Typography;

function generateParticles(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    size: Math.random() * 5 + 2,
    duration: Math.random() * 18 + 8,
    delay: Math.random() * 18,
    color: ['#667eea', '#00d2ff', '#764ba2', '#f093fb', '#4facfe', '#43e97b'][Math.floor(Math.random() * 6)],
  }));
}

interface Particle { id: number; left: string; size: number; duration: number; delay: number; color: string; }

function useCountUp(end: number, duration: number, startCounting: boolean) {
  const [count, setCount] = useState(0);
  const frameRef = useRef<number>(0);
  useEffect(() => {
    if (!startCounting) return;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setCount(Math.floor((1 - Math.pow(1 - progress, 3)) * end));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [end, duration, startCounting]);
  return count;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [particles] = useState<Particle[]>(() => generateParticles(50));
  const [searchValue, setSearchValue] = useState('');
  const [statsVisible, setStatsVisible] = useState(false);
  const [featureVisible, setFeatureVisible] = useState(false);
  const statsRef = useRef<HTMLDivElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);

  const paperCount = useCountUp(12860, 2000, statsVisible);
  const ideaCount = useCountUp(3847, 2500, statsVisible);
  const userCount = useCountUp(156, 1800, statsVisible);

  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setStatsVisible(true); observer.disconnect(); } }, { threshold: 0.3 });
    if (statsRef.current) observer.observe(statsRef.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setFeatureVisible(true); observer.disconnect(); } }, { threshold: 0.1 });
    if (featuresRef.current) observer.observe(featuresRef.current);
    return () => observer.disconnect();
  }, []);

  const handleSearch = useCallback(() => { if (searchValue.trim()) navigate(`/papers?q=${encodeURIComponent(searchValue.trim())}`); }, [searchValue, navigate]);

  const quickActions = [
    { key: 'chat', icon: <CommentOutlined />, label: 'AI 对话', desc: '与大模型对话探索研究方向', className: 'btn-chat', path: '/chat' },
    { key: 'papers', icon: <BookOutlined />, label: '论文库', desc: '检索与管理学术论文', className: 'btn-papers', path: '/papers' },
    { key: 'research', icon: <ExperimentOutlined />, label: '研究方向', desc: '自动化科研 Idea 生成', className: 'btn-research', path: '/research' },
    { key: 'writing', icon: <EditOutlined />, label: '写作助手', desc: '智能引用与论文写作', className: 'btn-writing', path: '/writing' },
  ];

  const features = [
    { icon: <SearchOutlined />, bg: 'linear-gradient(135deg, #667eea, #764ba2)', title: '智能论文检索', desc: '接入 arXiv 等学术源，支持关键词和语义搜索，自动抓取论文元数据和全文。' },
    { icon: <ThunderboltOutlined />, bg: 'linear-gradient(135deg, #f093fb, #f5576c)', title: 'AI Idea 生成', desc: '基于知识库中该方向的前沿论文，分析研究 gap，自动生成创新性研究想法。' },
    { icon: <GlobalOutlined />, bg: 'linear-gradient(135deg, #4facfe, #00f2fe)', title: '知识库管理', desc: '持久化分类存储论文，支持向量语义搜索，构建课题组专属科研知识图谱。' },
    { icon: <RocketOutlined />, bg: 'linear-gradient(135deg, #43e97b, #38f9d7)', title: '论文写作辅助', desc: '智能引用推荐，自动生成 Related Work，BibTeX 管理，格式规范检查。' },
  ];

  return (
    <div style={{ margin: -24 }}>
      {/* ═══════ Hero ═══════ */}
      <section className="hero-section">
        {/* Animated gradient orbs */}
        <div className="hero-orbs">
          <div className="hero-orb hero-orb-1" />
          <div className="hero-orb hero-orb-2" />
          <div className="hero-orb hero-orb-3" />
        </div>
        {/* Particles */}
        <div className="particles-bg">
          {particles.map(p => (
            <div key={p.id} className="particle" style={{ left: p.left, width: p.size, height: p.size, background: p.color, animationDuration: `${p.duration}s`, animationDelay: `${p.delay}s` }} />
          ))}
        </div>
        {/* Floating shapes */}
        <div className="geo-shape" style={{ width: 140, height: 140, border: '2px solid rgba(102,126,234,0.5)', borderRadius: '30% 70% 70% 30% / 30% 30% 70% 70%' }} />
        <div className="geo-shape" style={{ width: 90, height: 90, border: '2px solid rgba(0,210,255,0.4)', borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' }} />
        <div className="geo-shape" style={{ width: 110, height: 110, border: '2px solid rgba(240,147,251,0.4)', borderRadius: '40% 60% 70% 30% / 40% 50% 60% 50%' }} />
        <div className="geo-shape" style={{ width: 70, height: 70, border: '2px solid rgba(67,233,123,0.3)', borderRadius: '50% 50% 30% 70% / 25% 65% 35% 75%' }} />

        <div className="hero-content">
          {/* Badge */}
          <div className="hero-badge">
            <StarFilled style={{ color: '#faad14', fontSize: 14 }} />
            <span>由 DeepSeek V4 Pro 驱动</span>
            <FireOutlined style={{ color: '#ff4d4f', fontSize: 12, marginLeft: 6 }} />
            <span style={{ color: 'rgba(255,255,255,0.7)' }}>全新升级</span>
          </div>

          <h1 className="hero-title">Auto-Research-DS</h1>
          <p className="hero-subtitle">
            新一代 AI 驱动的自动化科研工作流系统。从论文检索、知识沉淀到 Idea 生成与论文写作，全流程助力你的研究工作。
          </p>

          {/* Search */}
          <div className="search-bar-wrapper">
            <Input size="large" placeholder="搜索论文，例如：Transformer, RLHF, Multimodal..." prefix={<SearchOutlined style={{ color: '#999' }} />} value={searchValue}
              onChange={e => setSearchValue(e.target.value)} onPressEnter={handleSearch}
              style={{ borderRadius: 50, height: 56, fontSize: 16, boxShadow: '0 8px 40px rgba(102,126,234,0.3), 0 0 0 4px rgba(102,126,234,0.1)' }}
              suffix={<Button type="primary" shape="circle" icon={<ArrowRightOutlined />} onClick={handleSearch} style={{ width: 40, height: 40, background: 'linear-gradient(135deg,#667eea,#764ba2)', border: 'none' }} />}
            />
          </div>

          {/* Quick actions */}
          <div className="quick-actions">
            {quickActions.map(action => (
              <button key={action.key} className={`quick-action-btn ${action.className}`} onClick={() => navigate(action.path)}>
                <span className="btn-icon">{action.icon}</span>
                <span className="btn-text">
                  <strong>{action.label}</strong>
                  <Text style={{ display: 'block', fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 2 }}>{action.desc}</Text>
                </span>
                <ArrowRightOutlined className="btn-arrow" style={{ opacity: 0, transition: 'all 0.3s', marginLeft: 8 }} />
              </button>
            ))}
          </div>

          {/* Scroll hint */}
          <div className="scroll-hint">
            <span>向下滚动探索</span>
            <div className="scroll-mouse"><div className="scroll-wheel" /></div>
          </div>
        </div>
      </section>

      {/* ═══════ Stats ═══════ */}
      <section className="stats-section" ref={statsRef}>
        <div className="stats-grid">
          {[{ n: paperCount, l: '已收录论文', i: <BookOutlined /> }, { n: ideaCount, l: '生成研究 Idea', i: <BulbOutlined /> }, { n: userCount, l: '活跃课题组', i: <TeamOutlined /> }, { n: '24/7', l: '全天候运行', i: <ClockCircleOutlined /> }].map((s, i) => (
            <div key={i} className="stat-item" style={statsVisible ? { opacity: 1, transform: 'translateY(0)' } : {}}>
              <div className="stat-icon-wrap" style={{ background: `linear-gradient(135deg, ${['#667eea,#764ba2','#4facfe,#00f2fe','#f093fb,#f5576c','#43e97b,#38f9d7'][i]})` }}>
                {s.i}
              </div>
              <div className="stat-number">{typeof s.n === 'number' ? s.n.toLocaleString() + '+' : s.n}</div>
              <div className="stat-label">{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════ Features ═══════ */}
      <section className="features-section" ref={featuresRef}>
        <div className="features-header">
          <Tag color="purple" style={{ borderRadius: 20, padding: '2px 16px', fontSize: 13, marginBottom: 16 }}>核心功能</Tag>
          <h2>强大的科研助手</h2>
          <p>四大核心模块，覆盖科研全流程</p>
        </div>
        <Row gutter={[24, 24]} className="features-grid" style={{ maxWidth: 1200, margin: '0 auto' }}>
          {features.map((f, i) => (
            <Col xs={24} sm={12} lg={6} key={i}>
              <div className="feature-card-v2" onClick={() => navigate(quickActions[i].path)}
                style={featureVisible ? { opacity: 1, transform: 'translateY(0)', transitionDelay: `${i * 0.1}s` } : {}}>
                <div className="fc-icon" style={{ background: f.bg }}>{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
                <div className="fc-link">了解更多 <ArrowRightOutlined /></div>
              </div>
            </Col>
          ))}
        </Row>
      </section>

      {/* ═══════ Footer ═══════ */}
      <footer className="footer-section">
        <div className="footer-content">
          <div className="footer-brand">
            <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg,#667eea,#764ba2)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <RocketOutlined style={{ color: '#fff', fontSize: 18 }} />
            </div>
            <Text strong>Auto-Research-DS</Text>
          </div>
          <Text type="secondary" style={{ fontSize: 13 }}>© 2026 · 由 DeepSeek V4 Pro 驱动 · 为课题组打造的新一代 AI 科研平台</Text>
          <Space size={16} style={{ marginTop: 12 }}>
            {quickActions.map(a => <Button key={a.key} type="text" size="small" onClick={() => navigate(a.path)} style={{ color: '#888' }}>{a.label}</Button>)}
          </Space>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
