import pandas as pd
import streamlit as st
import csv
import io

def detect_delimiter(file):
    try:
        file.seek(0)
        sample = file.read(1024).decode('latin-1')
        file.seek(0)
        sniffer = csv.Sniffer()
        return sniffer.sniff(sample).delimiter
    except:
        return ','

def generate_name_from_email(row):
    if any(str(row[field]).strip() not in ['', 'nan'] for field in ['First Name', 'Last Name', 'Nickname']):
        return row
    
    email = str(row.get('E-mail 1 - Value', '')).split('@')[0]
    clean = ''.join([c for c in email if c.isalpha() or c in '._- ']).strip()
    
    for sep in ['.', '_', '-', ' ']:
        if sep in clean:
            parts = [p.strip().title() for p in clean.split(sep) if p.strip()]
            if parts:
                row['First Name'] = parts[0] if len(parts) > 0 else ''
                row['Last Name'] = parts[1] if len(parts) > 1 else ''
                row['File As'] = ' '.join(parts[:2]).strip()
                break
    else:
        if clean:
            row['First Name'] = clean.title()
            row['File As'] = clean.title()
    
    return row

def map_columns(df):
    column_mapping = {
        # İsim Bilgileri
        'Adı': 'First Name',
        'Soyadı': 'Last Name',
        'Takma adı': 'Nickname',
        'Görüntülenecek ad': 'File As',
        
        # İletişim Bilgileri
        'Birinci e-posta': 'E-mail 1 - Value',
        'İkinci e-posta': 'E-mail 2 - Value',
        'Cep telefonu': 'Phone 1 - Value',
        'İş telefonu': 'Phone 2 - Value',
        'Ev telefonu': 'Phone 3 - Value',
        
        # Kurumsal Bilgiler
        'Kurum': 'Organization Name',
        'İş unvanı': 'Organization Title', 
        'Bölüm': 'Organization Department',
        
        # Adres Bilgileri
        'Ev adresi': 'Address 1 - Street',
        'Ev adresi 2': 'Address 1 - Extended Address',
        'Ev şehri': 'Address 1 - City',
        'Ev bölgesi': 'Address 1 - Region',
        'Ev posta kodu': 'Address 1 - Postal Code',
        'Ev ülkesi': 'Address 1 - Country',
        
        # Diğer
        'Doğum yılı': 'Birth Year',
        'Doğum ayı': 'Birth Month',
        'Doğum günü': 'Birth Day',
        'Web sayfası 1': 'Website 1 - Value',
        'Web sayfası 2': 'Website 2 - Value',
        'Notlar': 'Notes'
    }

    new_df = pd.DataFrame()
    
    # Temel eşleştirmeler
    for old_col, new_col in column_mapping.items():
        new_df[new_col] = df[old_col].fillna('').astype(str).str.strip() if old_col in df.columns else ''

    # Zorunlu etiketler
    labels_mapping = {
        'E-mail 1 - Label': 'Work',
        'E-mail 2 - Label': 'Home',
        'Phone 1 - Label': 'Mobile',
        'Phone 2 - Label': 'Work',
        'Phone 3 - Label': 'Home',
        'Website 1 - Label': 'Work',
        'Website 2 - Label': 'Home',
        'Address 1 - Label': 'Home'
    }
    
    for col, label in labels_mapping.items():
        new_df[col] = label

    # Doğum tarihini formatla
    try:
        new_df['Birth Month'] = pd.to_numeric(new_df['Birth Month'], errors='coerce').astype(int)
        new_df['Birth Day'] = pd.to_numeric(new_df['Birth Day'], errors='coerce').astype(int)
        new_df['Birthday'] = new_df.apply(
            lambda row: f"{row['Birth Month']:02d}/{row['Birth Day']:02d}/{row['Birth Year']}"
            if not pd.isna(row['Birth Year']) and not pd.isna(row['Birth Month']) and not pd.isna(row['Birth Day'])
            else '', axis=1
        )
    except:
        new_df['Birthday'] = ''

    # Adres formatlama
    new_df['Address 1 - Formatted'] = new_df.apply(
        lambda row: f"{row['Address 1 - Street']}\n{row['Address 1 - City']} {row['Address 1 - Postal Code']}\n{row['Address 1 - Country']}".strip(),
        axis=1
    )

    # İsim üretme
    new_df = new_df.apply(generate_name_from_email, axis=1)
    
    # Google sütun yapısı
    google_columns = [
        'First Name', 'Middle Name', 'Last Name', 'Phonetic First Name',
        'Phonetic Middle Name', 'Phonetic Last Name', 'Name Prefix',
        'Name Suffix', 'Nickname', 'File As', 'Organization Name',
        'Organization Title', 'Organization Department', 'Birthday', 'Notes',
        'Photo', 'Labels', 'E-mail 1 - Label', 'E-mail 1 - Value',
        'E-mail 2 - Label', 'E-mail 2 - Value', 'Phone 1 - Label',
        'Phone 1 - Value', 'Phone 2 - Label', 'Phone 2 - Value',
        'Phone 3 - Label', 'Phone 3 - Value', 'Address 1 - Label',
        'Address 1 - Formatted', 'Address 1 - Street', 'Address 1 - City',
        'Address 1 - PO Box', 'Address 1 - Region', 'Address 1 - Postal Code',
        'Address 1 - Country', 'Address 1 - Extended Address',
        'Website 1 - Label', 'Website 1 - Value'
    ]

    # Eksik sütunları ekle
    for col in google_columns:
        if col not in new_df.columns:
            new_df[col] = ''

    return new_df[google_columns]

# Streamlit Arayüz
st.title("📇 Google Kişiler CSV Dönüştürücü")
uploaded_file = st.file_uploader("CSV dosyası yükleyin", type="csv")

if uploaded_file:
    try:
        uploaded_file.seek(0)
        delimiter = detect_delimiter(uploaded_file)
        
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=delimiter, encoding='utf-8')
        
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=delimiter, encoding='latin-1')
        
    except pd.errors.EmptyDataError:
        st.error("Hata: Dosya boş!")
        st.stop()
        
    except Exception as e:
        st.error(f"Hata: {str(e)}")
        st.stop()
    
    if not df.empty:
        with st.spinner('Dönüştürülüyor...'):
            converted_df = map_columns(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Orijinal Veri")
            st.dataframe(df.head(3))
        
        with col2:
            st.subheader("Google Formatı")
            st.dataframe(converted_df.head(3))
        
        csv_buffer = io.StringIO()
        converted_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 İndir",
            data=csv_buffer.getvalue().encode('utf-8-sig'),
            file_name="google_contacts.csv",
            mime="text/csv"
        )
    else:
        st.error("Hata: Geçerli veri bulunamadı!")
