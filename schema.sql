-- EnterprisePulse schema + seed. Run in Supabase SQL editor.
-- Also create a public storage bucket named "documents".
create table departments(id int primary key, name text not null);
create table employees(id int primary key, name text, email text unique,
  role text check (role in ('employee','manager','admin')), dept_id int references departments,
  designation text, skills text[]);
create table projects(id int primary key, name text, manager_id int references employees, dept_id int references departments,
  status text default 'active', progress int, deadline date, budget numeric, spent numeric);
create table project_members(project_id int references projects, employee_id int references employees, primary key(project_id, employee_id));
create table tasks(id serial primary key, project_id int references projects, title text, description text,
  assignee_id int references employees, priority text, due date, status text);
create table documents(id serial primary key, name text, category text, dept_id int references departments,
  project_id int references projects, uploader_id int references employees,
  access text check (access in ('Company','Department','Project Team','Restricted')),
  version text default 'v1.0', description text, path text, created date default current_date);
create table document_versions(id serial primary key, document_id int references documents, version text, note text, created date default current_date);
create table issues(id serial primary key, project_id int references projects, title text, priority text,
  owner_id int references employees, status text, created date default current_date);
create table activities(id serial primary key, actor_id int references employees, action text,
  project_id int, document_id int, at timestamptz default now());
create table notifications(id serial primary key, employee_id int, text text, project_id int, created timestamptz default now());

insert into departments values (1,'Engineering'),(2,'Quality Assurance'),(3,'Human Resources'),(4,'Finance');
insert into employees values
(1,'Kavita Menon','kavita.menon@northwind.example','admin',3,'Head of Operations',array['Governance','Process']),
(2,'Rahul Sharma','rahul.sharma@northwind.example','manager',1,'Engineering Manager',array['Python','System design']),
(3,'Neha Sharma','neha.sharma@northwind.example','employee',2,'QA Lead',array['Test automation','Selenium']),
(4,'Arjun Deshpande','arjun.deshpande@northwind.example','employee',1,'Backend Developer',array['Python','PostgreSQL']),
(5,'Priya Iyer','priya.iyer@northwind.example','employee',1,'Frontend Developer',array['React','Accessibility']),
(6,'Sameer Kulkarni','sameer.kulkarni@northwind.example','manager',4,'Finance Manager',array['Budgeting','Forecasting']),
(7,'Anita Joshi','anita.joshi@northwind.example','employee',3,'HR Business Partner',array['Policy','Onboarding']),
(8,'Vikram Patil','vikram.patil@northwind.example','employee',2,'QA Engineer',array['Python','API testing']);
insert into projects values
(1,'Project Alpha',2,1,'active',72,current_date+12,1800000,1350000),
(2,'Project Beta',2,1,'active',38,current_date+45,2400000,900000),
(3,'Vendor Portal Revamp',6,4,'active',55,current_date+8,900000,610000),
(4,'HR Onboarding Automation',1,3,'completed',100,current_date-20,500000,470000);
insert into project_members values (1,2),(1,3),(1,4),(1,5),(1,8),(2,2),(2,4),(2,5),(3,6),(3,5),(3,7),(4,1),(4,7);
insert into tasks(project_id,title,description,assignee_id,priority,due,status) values
(1,'Regression testing of billing module','Full regression pass before release',3,'High',current_date-3,'In Progress'),
(1,'Fix invoice rounding defect','Rounding error found in QA cycle 2',4,'High',current_date-1,'Blocked'),
(1,'Update API documentation','Document v2 endpoints',4,'Medium',current_date+5,'To Do'),
(1,'Performance test scripts','Load profile for 500 users',8,'Medium',current_date+7,'In Progress'),
(1,'Dashboard accessibility audit','WCAG 2.1 AA review',5,'Low',current_date+10,'To Do'),
(1,'Database migration script','Migrate schema to v2',4,'High',current_date-8,'Completed'),
(2,'Service architecture review','Review with platform team',2,'High',current_date+9,'In Progress'),
(2,'Authentication service','SSO integration',4,'High',current_date+20,'To Do'),
(2,'Design system tokens','Colour and type tokens',5,'Medium',current_date+14,'In Progress'),
(3,'Vendor onboarding form','Multi step form',5,'High',current_date+3,'In Progress'),
(3,'Budget approval workflow','Approval routing rules',6,'High',current_date-2,'To Do'),
(3,'Vendor policy content','Update compliance copy',7,'Low',current_date+6,'To Do'),
(4,'Rollout training sessions','Held for all departments',7,'Medium',current_date-25,'Completed');
insert into documents(name,category,dept_id,project_id,uploader_id,access,version,description,path,created) values
('Project Alpha Testing Report.pdf','Reports',2,1,3,'Project Team','v1.1','Testing findings from QA cycle 2, including the invoice rounding defect',null,current_date-1),
('Project Alpha Requirements.docx','Technical',1,1,2,'Project Team','v2.0','Functional requirements for billing v2',null,current_date-30),
('Leave Policy 2026.pdf','Policies',3,null,7,'Company','v3.0','Annual, sick and parental leave rules for all employees',null,current_date-60),
('Expense Reimbursement SOP.pdf','SOPs',4,null,6,'Company','v1.2','How to file and approve expense claims',null,current_date-90),
('Project Beta Architecture Notes.md','Technical',1,2,2,'Project Team','v1.0','Service boundaries and data flow for Beta',null,current_date-9),
('Q3 Budget Review.xlsx','Financial',4,3,6,'Restricted','v1.0','Quarterly spend against budget',null,current_date-5),
('Engineering Code Review Guidelines.pdf','Guidelines',1,null,2,'Department','v1.4','Review standards for engineering',null,current_date-40),
('Vendor Portal Meeting Minutes.docx','Meeting Minutes',4,3,7,'Project Team','v1.0','Decisions from vendor portal kickoff',null,current_date-12);
insert into document_versions(document_id,version,note,created) values
(1,'v1.0','First draft after cycle 1',current_date-10),(1,'v1.1','Added billing defects',current_date-1),
(2,'v1.0','Initial requirements',current_date-70),(2,'v1.1','Scope changes',current_date-50),(2,'v2.0','Billing v2 scope',current_date-30);
insert into issues(project_id,title,priority,owner_id,status,created) values
(1,'Invoice totals off by one paisa on bulk orders','Critical',4,'Open',current_date-4),
(1,'Report export times out above 5000 rows','Medium',8,'Open',current_date-6),
(2,'SSO provider sandbox unavailable','High',4,'Open',current_date-2),
(3,'Approval routing ambiguous for joint budgets','Medium',6,'Open',current_date-3);
insert into activities(actor_id,action,project_id,document_id,at) values
(3,'uploaded Project Alpha Testing Report v1.1',1,1,now()-interval '1 day'),
(4,'marked Fix invoice rounding defect as Blocked',1,null,now()-interval '2 days'),
(2,'changed the Project Alpha deadline',1,null,now()-interval '3 days'),
(7,'uploaded Vendor Portal Meeting Minutes',3,8,now()-interval '12 days'),
(6,'uploaded Q3 Budget Review',3,6,now()-interval '5 days');
insert into notifications(employee_id,text,project_id,created) values
(null,'Project Alpha deadline is approaching',1,now()-interval '1 day'),
(3,'Regression testing of billing module is overdue',1,now()-interval '2 days'),
(2,'Neha Sharma uploaded Project Alpha Testing Report',1,now()-interval '1 day');
