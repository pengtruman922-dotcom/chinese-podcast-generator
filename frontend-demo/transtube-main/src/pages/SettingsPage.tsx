import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

interface Config {
  asr: {
    appid: string;
    access_token: string;
    poll_interval: number;
    hotwords: string[];
  };
  translate: {
    api_key: string;
    base_url: string;
    model: string;
    system_prompt: string;
  };
  tts: {
    appid: string;
    access_token: string;
    resource_id: string;
    speaker_map: Record<string, string>;
    concurrency: number;
    speech_rate: number;
  };
  tos: {
    access_key: string;
    secret_key: string;
    endpoint: string;
    region: string;
    bucket_name: string;
  };
}

interface VoiceDatabase {
  [resourceId: string]: {
    [category: string]: Array<[string, string]>;
  };
}

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const [config, setConfig] = useState<Config | null>(null);
  const [voiceDatabase, setVoiceDatabase] = useState<VoiceDatabase>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
    fetchVoiceDatabase();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/config`);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchVoiceDatabase = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-database`);
      if (response.ok) {
        const data = await response.json();
        setVoiceDatabase(data);
      }
    } catch (error) {
      console.error('Failed to fetch voice database:', error);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config_data: config })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(result.message || '配置保存成功！');
      } else {
        const error = await response.json();
        alert(`保存失败: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (section: keyof Config, key: string, value: any) => {
    if (!config) return;
    setConfig({
      ...config,
      [section]: {
        ...config[section],
        [key]: value
      }
    });
  };

  const updateSpeakerMap = (speaker: string, voiceId: string) => {
    if (!config) return;
    setConfig({
      ...config,
      tts: {
        ...config.tts,
        speaker_map: {
          ...config.tts.speaker_map,
          [speaker]: voiceId
        }
      }
    });
  };

  const getAvailableVoices = (resourceId: string): Array<[string, string]> => {
    const voices: Array<[string, string]> = [];
    if (voiceDatabase[resourceId]) {
      Object.values(voiceDatabase[resourceId]).forEach(categoryVoices => {
        voices.push(...categoryVoices);
      });
    }
    return voices;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="text-center py-12 text-red-600">
        加载配置失败
      </div>
    );
  }

  const availableVoices = getAvailableVoices(config.tts.resource_id);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:underline mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            返回任务列表
          </button>
          <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
          <p className="text-gray-600 mt-2">管理系统配置参数</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          {saving ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              保存中...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
              保存配置
            </>
          )}
        </button>
      </div>

      <div className="space-y-6">
        {/* ASR配置 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            ASR 语音识别配置
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">App ID</label>
              <input
                type="text"
                value={config.asr.appid}
                onChange={(e) => updateConfig('asr', 'appid', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
              <input
                type="password"
                value={config.asr.access_token}
                onChange={(e) => updateConfig('asr', 'access_token', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">轮询间隔（秒）</label>
              <input
                type="number"
                value={config.asr.poll_interval}
                onChange={(e) => updateConfig('asr', 'poll_interval', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* 翻译配置 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
            AI 翻译配置
          </h2>
          <div className="grid grid-cols-1 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <input
                type="password"
                value={config.translate.api_key}
                onChange={(e) => updateConfig('translate', 'api_key', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API地址</label>
              <input
                type="text"
                value={config.translate.base_url}
                onChange={(e) => updateConfig('translate', 'base_url', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">模型</label>
              <input
                type="text"
                value={config.translate.model}
                onChange={(e) => updateConfig('translate', 'model', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">系统提示词</label>
              <textarea
                value={config.translate.system_prompt}
                onChange={(e) => updateConfig('translate', 'system_prompt', e.target.value)}
                rows={8}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 font-mono text-sm"
              />
            </div>
          </div>
        </div>

        {/* TTS配置 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
            TTS 语音合成配置
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">App ID</label>
              <input
                type="text"
                value={config.tts.appid}
                onChange={(e) => updateConfig('tts', 'appid', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
              <input
                type="password"
                value={config.tts.access_token}
                onChange={(e) => updateConfig('tts', 'access_token', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">资源版本</label>
              <select
                value={config.tts.resource_id}
                onChange={(e) => updateConfig('tts', 'resource_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                {Object.keys(voiceDatabase).map(resourceId => (
                  <option key={resourceId} value={resourceId}>
                    {resourceId === 'seed-tts-2.0' ? 'TTS 2.0 版本' : 'TTS 1.0 版本'}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">并发数 (1-10)</label>
              <input
                type="number"
                min="1"
                max="10"
                value={config.tts.concurrency}
                onChange={(e) => updateConfig('tts', 'concurrency', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">语速 (-50到100)</label>
              <input
                type="number"
                min="-50"
                max="100"
                value={config.tts.speech_rate}
                onChange={(e) => updateConfig('tts', 'speech_rate', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
          </div>
          
          {/* 音色映射 */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">音色映射</label>
            <div className="space-y-3">
              {Object.entries(config.tts.speaker_map).map(([speaker, voiceId]) => (
                <div key={speaker} className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">{speaker}</label>
                    <input
                      type="text"
                      value={speaker}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">音色</label>
                    <select
                      value={voiceId}
                      onChange={(e) => updateSpeakerMap(speaker, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    >
                      {availableVoices.map(([name, id]) => (
                        <option key={id} value={id}>{name}</option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* TOS配置 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
            TOS 对象存储配置
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Key</label>
              <input
                type="password"
                value={config.tos.access_key}
                onChange={(e) => updateConfig('tos', 'access_key', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Secret Key</label>
              <input
                type="password"
                value={config.tos.secret_key}
                onChange={(e) => updateConfig('tos', 'secret_key', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint</label>
              <input
                type="text"
                value={config.tos.endpoint}
                onChange={(e) => updateConfig('tos', 'endpoint', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
              <input
                type="text"
                value={config.tos.region}
                onChange={(e) => updateConfig('tos', 'region', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Bucket名称</label>
              <input
                type="text"
                value={config.tos.bucket_name}
                onChange={(e) => updateConfig('tos', 'bucket_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
