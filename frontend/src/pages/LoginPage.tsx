import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Typography, message, Divider } from 'antd';
import { UserOutlined, LockOutlined, RocketOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/useAuthStore';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('登录成功！');
      navigate('/');
    } catch (e: any) {
      message.error(e.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="auth-page"
      style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0e27 0%, #1a1040 50%, #0d1b3e 100%)',
      }}
    >
      <div
        className="auth-card"
        style={{
          background: '#fff', padding: '48px 40px', borderRadius: 16,
          boxShadow: '0 20px 80px rgba(0,0,0,0.3)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <RocketOutlined style={{ fontSize: 40, color: '#667eea', marginBottom: 12 }} />
          <Title level={3} style={{ marginBottom: 4 }}>Auto-Research-DS</Title>
          <Text type="secondary">自动化科研工作流系统</Text>
        </div>

        <Form layout="vertical" onFinish={handleSubmit} size="large">
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名或邮箱' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名或邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider plain><Text type="secondary" style={{ fontSize: 13 }}>还没有账号？</Text></Divider>

        <div style={{ textAlign: 'center' }}>
          <Link to="/register">
            <Button type="link" style={{ padding: 0 }}>注册新账号 →</Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
