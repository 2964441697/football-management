-- 足球管理系统数据库初始化脚本
-- 运行此脚本创建数据库和所有表

CREATE DATABASE IF NOT EXISTS football_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE football_db;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  avatar TEXT,
  role VARCHAR(30) NOT NULL DEFAULT 'viewer',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_username (username),
  INDEX idx_email (email),
  INDEX idx_role (role)
);

-- 球队表
CREATE TABLE IF NOT EXISTS teams (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  logo VARCHAR(255),
  home_stadium VARCHAR(120),
  founded_year INT,
  budget DECIMAL(18,2) DEFAULT 0.00,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_name (name)
);

-- 球员表
CREATE TABLE IF NOT EXISTS players (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  age INT,
  nationality VARCHAR(80),
  position VARCHAR(30),
  height_cm INT,
  avatar LONGTEXT,
  team_id INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
  INDEX idx_name (name),
  INDEX idx_nationality (nationality),
  INDEX idx_position (position),
  INDEX idx_team_id (team_id),
  INDEX idx_player_team_position (team_id, position),
  INDEX idx_player_nationality_position (nationality, position)
);

-- 赛季表
CREATE TABLE IF NOT EXISTS seasons (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  start_date DATE,
  end_date DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 比赛表
CREATE TABLE IF NOT EXISTS matches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  season_id INT,
  home_team_id INT,
  away_team_id INT,
  start_time DATETIME,
  venue VARCHAR(120),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE SET NULL,
  FOREIGN KEY (home_team_id) REFERENCES teams(id) ON DELETE SET NULL,
  FOREIGN KEY (away_team_id) REFERENCES teams(id) ON DELETE SET NULL,
  INDEX idx_season_id (season_id),
  INDEX idx_start_time (start_time),
  INDEX idx_venue (venue),
  INDEX idx_match_teams (home_team_id, away_team_id)
);

-- 赛事表
CREATE TABLE IF NOT EXISTS competitions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  type VARCHAR(50),
  season_id INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE SET NULL,
  INDEX idx_name (name),
  INDEX idx_type (type),
  INDEX idx_season_id (season_id)
);

-- 教练表
CREATE TABLE IF NOT EXISTS coaches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  nationality VARCHAR(80),
  date_of_birth DATE,
  role VARCHAR(50) DEFAULT '主教练',
  avatar TEXT,
  team_id INT,
  hire_date DATE,
  salary DECIMAL(18,2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
  INDEX idx_name (name),
  INDEX idx_team_id (team_id)
);

-- 合同表
CREATE TABLE IF NOT EXISTS contracts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  player_id INT,
  team_id INT,
  start_date DATE,
  end_date DATE,
  salary DECIMAL(18,2),
  release_clause DECIMAL(18,2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  INDEX idx_player_id (player_id),
  INDEX idx_team_id (team_id),
  INDEX idx_start_date (start_date),
  INDEX idx_end_date (end_date)
);

-- 转会表
CREATE TABLE IF NOT EXISTS transfers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  player_id INT,
  from_team_id INT,
  to_team_id INT,
  fee DECIMAL(18,2),
  transfer_date DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
  FOREIGN KEY (from_team_id) REFERENCES teams(id) ON DELETE SET NULL,
  FOREIGN KEY (to_team_id) REFERENCES teams(id) ON DELETE SET NULL,
  INDEX idx_player_id (player_id),
  INDEX idx_from_team_id (from_team_id),
  INDEX idx_to_team_id (to_team_id),
  INDEX idx_transfer_date (transfer_date)
);

-- 比赛阵容表
CREATE TABLE IF NOT EXISTS match_lineups (
  id INT AUTO_INCREMENT PRIMARY KEY,
  match_id INT,
  team_id INT,
  player_id INT,
  is_starting TINYINT(1) DEFAULT 0,
  shirt_number INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
  INDEX idx_match_id (match_id),
  INDEX idx_team_id (team_id),
  INDEX idx_player_id (player_id)
);

-- 比赛事件表
CREATE TABLE IF NOT EXISTS match_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  match_id INT,
  minute INT,
  event_type VARCHAR(50),
  player_id INT,
  related_player_id INT,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE SET NULL,
  FOREIGN KEY (related_player_id) REFERENCES players(id) ON DELETE SET NULL,
  INDEX idx_match_id (match_id),
  INDEX idx_event_type (event_type),
  INDEX idx_player_id (player_id)
);

-- 比赛统计表
CREATE TABLE IF NOT EXISTS match_stats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  match_id INT,
  team_id INT,
  possession DECIMAL(5,2),
  shots INT,
  shots_on_target INT,
  passes INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  INDEX idx_match_id (match_id),
  INDEX idx_team_id (team_id)
);

-- 球员统计表
CREATE TABLE IF NOT EXISTS player_stats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  player_id INT,
  season_id INT,
  matches_played INT DEFAULT 0,
  goals INT DEFAULT 0,
  assists INT DEFAULT 0,
  yellow_cards INT DEFAULT 0,
  red_cards INT DEFAULT 0,
  minutes_played INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
  FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE SET NULL,
  INDEX idx_player_id (player_id),
  INDEX idx_season_id (season_id),
  INDEX idx_player_season_stats (player_id, season_id)
);

-- 新闻表
CREATE TABLE IF NOT EXISTS news (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT,
  author_id INT,
  published_at DATETIME,
  category VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_title (title),
  INDEX idx_author_id (author_id),
  INDEX idx_published_at (published_at),
  INDEX idx_category (category)
);

-- 财务表
CREATE TABLE IF NOT EXISTS finances (
  id INT AUTO_INCREMENT PRIMARY KEY,
  team_id INT,
  category VARCHAR(100),
  amount DECIMAL(18,2),
  note TEXT,
  record_date DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  INDEX idx_team_id (team_id),
  INDEX idx_category (category),
  INDEX idx_record_date (record_date),
  INDEX idx_finance_team_category (team_id, category)
);

-- 训练计划表
CREATE TABLE IF NOT EXISTS training_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  team_id INT,
  title VARCHAR(200) NOT NULL,
  content TEXT,
  training_date DATE,
  duration_minutes INT,
  location VARCHAR(120),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  INDEX idx_team_id (team_id),
  INDEX idx_training_date (training_date)
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  username VARCHAR(100),
  action VARCHAR(200) NOT NULL,
  resource_type VARCHAR(100),
  resource_id INT,
  details TEXT,
  ip_address VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_user_id (user_id),
  INDEX idx_resource_type (resource_type),
  INDEX idx_created_at (created_at)
);

-- =====================================================
-- 种子数据
-- =====================================================

-- 插入用户
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@example.com', 'admin123', 'admin'),
('coach', 'coach@example.com', 'coach123', 'coach'),
('viewer', 'viewer@example.com', 'viewer123', 'viewer');

-- 插入球队
INSERT INTO teams (name, logo, home_stadium, founded_year, budget) VALUES
('皇家马德里', 'https://example.com/logos/real_madrid.png', '伯纳乌球场', 1902, 500000000),
('巴塞罗那', 'https://example.com/logos/barcelona.png', '诺坎普球场', 1899, 450000000),
('拜仁慕尼黑', 'https://example.com/logos/bayern.png', '安联球场', 1900, 400000000),
('利物浦', 'https://example.com/logos/liverpool.png', '安菲尔德球场', 1892, 350000000),
('曼城', 'https://example.com/logos/manchester_city.png', '伊蒂哈德球场', 1880, 380000000),
('巴黎圣日耳曼', 'https://example.com/logos/psg.png', '王子公园球场', 1970, 320000000),
('曼联', 'https://example.com/logos/manchester_united.png', '老特拉福德球场', 1878, 360000000),
('尤文图斯', 'https://example.com/logos/juventus.png', '都灵安联体育场', 1897, 280000000);

-- 插入球员
INSERT INTO players (name, age, nationality, position, height_cm, team_id) VALUES
('卡里姆·本泽马', 35, '法国', '前锋', 185, 1),
('卢卡·莫德里奇', 38, '克罗地亚', '中场', 174, 1),
('维尼修斯·儒尼奥尔', 23, '巴西', '前锋', 176, 1),
('费德里科·巴尔韦德', 26, '乌拉圭', '中场', 182, 1),
('罗伯特·莱万多夫斯基', 35, '波兰', '前锋', 184, 2),
('佩德里', 21, '西班牙', '中场', 174, 2),
('加维', 19, '西班牙', '中场', 173, 2),
('托马斯·穆勒', 34, '德国', '前锋', 186, 3),
('约书亚·基米希', 29, '德国', '中场', 177, 3),
('萨迪奥·马内', 32, '塞内加尔', '前锋', 175, 3),
('穆罕默德·萨拉赫', 32, '埃及', '前锋', 175, 4),
('达尔文·努涅斯', 24, '乌拉圭', '前锋', 187, 4),
('埃尔林·哈兰德', 24, '挪威', '前锋', 194, 5),
('凯文·德布劳内', 33, '比利时', '中场', 181, 5),
('基利安·姆巴佩', 25, '法国', '前锋', 178, 6),
('莱昂内尔·梅西', 37, '阿根廷', '前锋', 170, 6),
('布鲁诺·费尔南德斯', 30, '葡萄牙', '中场', 179, 7),
('马库斯·拉什福德', 26, '英格兰', '前锋', 180, 7),
('杜桑·弗拉霍维奇', 24, '塞尔维亚', '前锋', 190, 8),
('保罗·博格巴', 31, '法国', '中场', 191, 8);

-- 插入赛季
INSERT INTO seasons (name, start_date, end_date) VALUES
('2023-2024赛季', '2023-08-01', '2024-07-31'),
('2024-2025赛季', '2024-08-01', '2025-07-31'),
('2022-2023赛季', '2022-08-01', '2023-07-31');

-- 插入赛事
INSERT INTO competitions (name, type, season_id) VALUES
('西甲联赛', '联赛', 1),
('欧冠联赛', '杯赛', 1),
('国王杯', '杯赛', 1),
('西甲联赛', '联赛', 2),
('欧冠联赛', '杯赛', 2);

-- 插入教练
INSERT INTO coaches (name, nationality, date_of_birth, role, team_id, hire_date, salary) VALUES
('卡洛·安切洛蒂', '意大利', '1959-06-10', '主教练', 1, '2021-01-01', 15000000),
('哈维·埃尔南德斯', '西班牙', '1980-01-25', '主教练', 2, '2021-11-01', 8000000),
('托马斯·图赫尔', '德国', '1973-08-29', '主教练', 3, '2023-03-01', 12000000),
('于尔根·克洛普', '德国', '1967-06-16', '主教练', 4, '2015-10-01', 18000000),
('佩普·瓜迪奥拉', '西班牙', '1971-02-18', '主教练', 5, '2016-07-01', 20000000);

-- 插入比赛
INSERT INTO matches (season_id, home_team_id, away_team_id, start_time, venue) VALUES
(1, 1, 2, '2024-03-02 20:00:00', '伯纳乌球场'),
(1, 2, 1, '2024-10-26 20:00:00', '诺坎普球场'),
(1, 3, 4, '2024-04-10 20:00:00', '安联球场');

-- 插入合同
INSERT INTO contracts (player_id, team_id, start_date, end_date, salary, release_clause) VALUES
(1, 1, '2024-01-01', '2026-06-30', 25000000, 100000000),
(5, 2, '2022-07-01', '2026-06-30', 45000000, 200000000),
(13, 5, '2022-07-01', '2027-06-30', 35000000, 180000000);

-- 插入转会
INSERT INTO transfers (player_id, from_team_id, to_team_id, fee, transfer_date) VALUES
(10, 4, 3, 45000000, '2023-07-01'),
(13, 7, 5, 60000000, '2022-07-01'),
(19, 8, 3, 70000000, '2022-08-01');

-- 插入新闻
INSERT INTO news (title, content, published_at, category) VALUES
('皇家马德里夺得2024欧冠冠军', '皇家马德里在欧冠决赛中2-0击败多特蒙德，夺得队史第15座欧冠奖杯。', '2024-06-02', '赛事新闻'),
('哈兰德续约曼城至2029年', '挪威前锋埃尔林·哈兰德与曼城续约至2029年，周薪达到50万英镑。', '2024-05-15', '转会新闻'),
('姆巴佩加盟皇家马德里', '法国球星基利安·姆巴佩正式加盟皇家马德里，双方签约5年。', '2024-07-01', '转会新闻'),
('2024-2025赛季西甲联赛即将开幕', '新赛季西甲联赛将于8月中旬开战，各支球队正在积极备战。', '2024-07-20', '联赛新闻'),
('巴萨签下新星中场', '巴塞罗那官方宣布签下18岁天才中场，转会费5000万欧元。', '2024-07-25', '转会新闻');

-- 插入财务记录
INSERT INTO finances (team_id, category, amount, note, record_date) VALUES
(1, '比赛日收入', 15000000, '欧冠决赛奖金', '2024-06-30'),
(1, '球衣销售', 8000000, '本泽马球衣销量', '2024-06-30'),
(2, '转会收入', 45000000, '出售球员收入', '2024-07-15'),
(3, '赞助收入', 25000000, '球衣赞助', '2024-07-01'),
(4, '球员工资', -35000000, '月度工资支出', '2024-07-31');

-- 插入训练计划
INSERT INTO training_plans (team_id, title, content, training_date, duration_minutes, location) VALUES
(1, '赛季前体能训练', '高强度体能训练，包括有氧耐力和力量训练', '2024-07-15', 120, '训练基地'),
(2, '战术演练', '进攻战术和防守战术训练', '2024-07-20', 90, '诺坎普训练场'),
(5, '进攻配合训练', '前场配合和射门训练', '2024-07-22', 105, '伊蒂哈德训练中心');
