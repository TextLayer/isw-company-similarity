import csv
import json
from io import StringIO

import click
import psycopg2
from sqlalchemy.orm import sessionmaker

from isw.core.models.company_models import Company, CompanyFacts
from isw.core.services.database import Base, DatabaseService


@click.group()
def database():
    """Database management commands."""
    pass


@database.command()
def init():
    """Initialize database tables."""
    click.echo("Initializing database tables...")
    db = DatabaseService.get_instance()
    Base.metadata.create_all(db.engine)
    click.echo("✓ Tables created")


@database.command()
@click.argument('csv_file', type=click.Path(exists=True))
def load_companies(csv_file):
    """Load companies from CSV."""
    click.echo(f"Loading companies from {csv_file}...")
    
    db = DatabaseService.get_instance()
    Session = sessionmaker(bind=db.engine)
    session = Session()
    
    session.query(Company).delete()
    session.commit()
    
    companies_data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        companies_data = list(csv.DictReader(f))
    
    click.echo(f"Found {len(companies_data)} companies")
    
    def parse_float(val):
        return float(val) if val else None
    
    def parse_int(val):
        return int(float(val)) if val else None
    
    successful = 0
    with click.progressbar(companies_data, label='Importing') as bar:
        for row in bar:
            try:
                company = Company(
                    cik=int(row['cik']),
                    company_name=row['company_name'],
                    description=row.get('description'),
                    embedded_description=json.loads(row['embedded_description']),
                    total_revenue=parse_float(row.get('total_revenue')),
                    sic=row.get('sic'),
                    market_cap=parse_float(row.get('market_cap')),
                    full_time_employees=parse_int(row.get('full_time_employees')),
                    cluster=parse_int(row.get('cluster')),
                    umap_x=parse_float(row.get('umap_x')),
                    umap_y=parse_float(row.get('umap_y')),
                    norm_mcap=parse_int(row.get('norm_mcap')),
                    norm_tot_rev=parse_int(row.get('norm_tot_rev')),
                    norm_fte=parse_int(row.get('norm_fte')),
                    louvain_community=parse_int(row.get('louvain_community')),
                    leiden_community=parse_int(row.get('leiden_community')),
                )
                session.add(company)
                successful += 1
                
                if successful % 100 == 0:
                    session.commit()
            except Exception as e:
                click.echo(f"\nError: {e}", err=True)
                session.rollback()
    
    session.commit()
    session.close()
    click.echo(f"\n✓ Loaded {successful} companies")


@database.command()
@click.argument('csv_file', type=click.Path(exists=True))
def load_facts(csv_file):
    """Load company facts from CSV."""
    click.echo(f"Loading facts from {csv_file}...")
    
    db = DatabaseService.get_instance()
    Session = sessionmaker(bind=db.engine)
    session = Session()
    
    valid_ciks = {cik[0] for cik in session.query(Company.cik).all()}
    click.echo(f"Found {len(valid_ciks)} valid CIKs")
    session.close()
    
    conn = psycopg2.connect(db.database_url)
    cursor = conn.cursor()
    
    cursor.execute("TRUNCATE TABLE company_facts;")
    cursor.execute("ALTER TABLE company_facts ALTER COLUMN created_at SET DEFAULT NOW();")
    cursor.execute("ALTER TABLE company_facts ALTER COLUMN updated_at SET DEFAULT NOW();")
    conn.commit()
    
    buffer = StringIO()
    total = 0
    imported = 0
    
    click.echo("Processing rows...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total += 1
            
            try:
                cik = int(row['cik'])
                fact = row['companyFact'].strip()
                fiscal_year = row['fy'].strip()
                filing_period = row['fp'].strip()
                form_type = row['form'].strip()
                
                if not (cik in valid_ciks and fact and fiscal_year and filing_period and form_type):
                    continue
                
                buffer.write(f"{cik}\t{fact}\t{row['val']}\t{fiscal_year}\t{filing_period}\t{form_type}\n")
                imported += 1
                
                if total % 1000000 == 0:
                    click.echo(f"  {total:,} rows processed ({imported:,} valid)")
            except Exception:
                continue
    
    click.echo(f"Filtered {total:,} → {imported:,} valid facts")
    click.echo("Importing...")
    
    buffer.seek(0)
    cursor.copy_expert(
        """COPY company_facts (cik, fact, value, fiscal_year, filing_period, form_type)
        FROM STDIN WITH (FORMAT text, DELIMITER E'\\t')""",
        buffer
    )
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM company_facts;")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    click.echo(f"✓ Loaded {count:,} facts")


@database.command()
def status():
    """Show database status."""
    db = DatabaseService.get_instance()
    
    with db.session_scope() as session:
        companies = session.query(Company).count()
        facts = session.query(CompanyFacts).count()
        
        click.echo(f"\nCompanies: {companies:,}")
        click.echo(f"Facts: {facts:,}")

