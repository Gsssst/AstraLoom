import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, RocketOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/useAuthStore';

const { Title, Text } = Typography;

const RegisterPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const register = useAuthStore((s) => s.register);

  const handleSubmit = async (values: { username: string; email: string; password: string }) => {
    if (values.password.length < 6) {
      message.error('密码至少 6 位');
      return;
    }
    setLoading(true);
    try {
      await register(values.username, values.email, values.password);
      message.success('注册成功！');
      navigate('/');
    } catch (e: any) {
      message.error(e.message || '注册失败');
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
          <Title level={3} style={{ marginBottom: 4 }}>注册账号</Title>
          <Text type="secondary">加入 Auto-Research-DS</Text>
        </div>

        <Form layout="vertical" onFinish={handleSubmit} size="large">
          <Form.Item
            name="username"
            rules={[{ required: true, min: 3, message: '用户名至少 3 个字符' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, min: 6, message: '密码至少 6 位' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少 6 位）" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text type="secondary">已有账号？</Text>
          <Link to="/login">
            <Button type="link">返回登录</Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
