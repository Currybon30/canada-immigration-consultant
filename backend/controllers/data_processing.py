from tools.clean_text_lv2 import clean_content_Level2
from langchain.schema import Document
import re
import warnings
import pdfplumber
warnings.filterwarnings("ignore")


def detect_headers_and_footers(pdf_path):
    header = ""
    footers = []
    ref_link = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text_lines()
            
            if not header:
                header = txt[0]['text']
                
            footer = txt[-1]['text']
            if footer not in footers:
                footers.append(footer)
                
            ref_link = footer.split()[0]
                
    return header, footers, ref_link


def clean_content(content, txt_removed=None, header=None, footers=None):
    content = re.sub(r'[\ue000-\ueFFF]', '', content)
    content = re.sub(r'\n', ' ', content)            # Replace newlines with spaces
    content = re.sub(r'Date modified: \d\d\d\d-\d\d-\d\d', '', content)  # Remove date modified
    
    if txt_removed:
        for txt in txt_removed:
            content = content.replace(txt, '')

    if header is not None and footers is not None:
        content = content.replace(header, '')            # Remove header
        for footer in footers:
            content = content.replace(footer, '')        # Remove footers
            
    content = clean_content_Level2(content)

    return content


def extract_hyperlinks(pdf_path):
    hyperlinks = []
    with pdfplumber.open(pdf_path) as pdf:
        for _, page in enumerate(pdf.pages):
            for annotation in page.annots:
                if str(annotation['uri']).startswith(r'http://') or str(annotation['uri']).startswith(r'https://'):
                    uri = annotation.get("uri", None)
                    if uri:
                        # Get the bounding box coordinates for the link
                        x0, y0, x1, y1 = annotation['x0'], annotation['top'], annotation['x1'], annotation['bottom']
                        
                        # Extract text within the bounding box
                        text_content = ""
                        for char in page.chars:
                            if x0 <= char['x0'] and char['x1'] <= x1 and y0 <= char['top'] and char['bottom'] <= y1:
                                text_content += char.get('text', '')
                        
                        hyperlink = {
                            "uri": uri,
                            "text": text_content.strip()
                        }
                        hyperlinks.append(hyperlink)
    return hyperlinks


def check_tables(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Iterate over all pages in the PDF
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract tables from the current page
            tables = page.find_tables()

            # If no tables are found on the page, continue to the next page
            if not tables:
                continue

            # Check each table on the page
            for table in tables:
                # Get the number of rows and columns in the table
                num_rows = len(table.rows)
                num_columns = len(table.rows[0].cells) if table.rows else 0

                # Adjusted condition to check for at least 2 rows and 2 columns
                if num_rows >= 2 and num_columns >= 2:
                    return True  # Return True immediately if a matching table is found

    return False


def extract_table_content(pdf_path):
    is_headers = False
    headers = []
    table_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table:
                    continue
                
                for row in table:
                    if not is_headers:
                        headers = row
                        is_headers = True
                    else:
                        table_content.append(dict(zip(headers, row)))
    
    # Clean table content
    cleaned_table_content = [
        {clean_content(key): clean_content(value) for key, value in entry.items()} for entry in table_content
    ]
    
    # Remove empty entries
    cleaned_table_content = [entry for entry in cleaned_table_content if any(value.strip() for value in entry.values())]
    return cleaned_table_content


def calc_bbox_difference(line_bbox, table_bbox):
    x0, y0, x1, y1 = line_bbox
    x2, y2, x3, y3 = table_bbox
    return abs(x0 - x2) + abs(y0 - y2) + abs(x1 - x3) + abs(y1 - y3)


def best_matching_table(line_bbox, table_bboxes):
    best_index = None
    min_bbox_diff = float('inf')
    for index, table_bbox in enumerate(table_bboxes):
        bbox_diff = calc_bbox_difference(line_bbox, table_bbox)
        if bbox_diff < min_bbox_diff:
            min_bbox_diff = bbox_diff
            best_index = index
    return best_index        


def detect_section_with_content(pdf_path, skip_tags=None, category=None, txt_removed = None, header=None, footers=None):
    if skip_tags is None:
        skip_tags = []
    else:
        skip_tags = [tag.lower() for tag in skip_tags]
    
    sections_with_content = []
    current_section = None
    current_subsection = None
    current_content = []
    subsection_indexes = {}
    section_index = None
    tracked_line = None
    
    
    SECTION_MIN_SIZE = 28
    SECTION_MAX_SIZE = 29
    SUBSECTION_MIN_SIZE = 26
    SUBSECTION_MAX_SIZE = 27
    is_section = False
    

    with pdfplumber.open(pdf_path) as pdf:
        if not check_tables(pdf_path):
            is_section = [(line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= line['chars'][0]['size'] < SECTION_MAX_SIZE) for page in pdf.pages for line in page.extract_text_lines()]
            is_subsection = [(line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= line['chars'][0]['size'] < SUBSECTION_MAX_SIZE) for page in pdf.pages for line in page.extract_text_lines()]
            for page_num, page in enumerate(pdf.pages):
                text_with_coords = page.extract_text_lines()
                
                for i, line in enumerate(text_with_coords):
                    text = line['text']
                    
                    
                    if text == tracked_line:
                        continue
                    
                    if line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= line['chars'][0]['size'] < SECTION_MAX_SIZE:
                        if current_section and current_content:
                            if sections_with_content:
                                sections_with_content[-1]['content'] = ' '.join(current_content).strip()
                        if text.lower() not in skip_tags:  # Skip section if in skip_tags
                            current_section = line['text']
                            next_is_section = (i + 1 < len(text_with_coords)
                                and text_with_coords[i + 1]['chars'][0]['fontname'].find("Lato-Bold")
                                and SECTION_MIN_SIZE <= text_with_coords[i + 1]['chars'][0]['size'] < SECTION_MAX_SIZE
                                )
                            if next_is_section:
                                section_title = text + " " + text_with_coords[i + 1]['text']
                                current_section = section_title
                                tracked_line = text_with_coords[i + 1]['text']
                            else:
                                if footers:
                                    last_line = text_with_coords[-2]['text']
                                    
                                    if last_line and last_line == current_section:
                                        if page_num + 1 < len(pdf.pages):
                                            next_page = pdf.pages[page_num + 1]
                                            next_page_lines = next_page.extract_text_lines()
                                            if header:
                                                first_line = next_page_lines[1]
                                                if first_line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= first_line['chars'][0]['size'] < SECTION_MAX_SIZE:
                                                    section_title = text + " " + first_line['text']
                                                    current_section = section_title
                                                    tracked_line = first_line['text']
                            current_content = []
                            if category != None:
                                sections_with_content.append({
                                    'tags': category,
                                    'section': current_section,
                                    'subsections': [],
                                    'content': ''
                                })
                            else:
                                sections_with_content.append({
                                    'tags': [],
                                    'section': current_section,
                                    'subsections': [],
                                    'content': ''
                                })
                            section_index = len(sections_with_content) - 1
                            subsection_indexes = {}
                    elif line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= line['chars'][0]['size'] < SUBSECTION_MAX_SIZE:
                        if current_subsection and current_content:
                            subsection_content = current_subsection + ": " + clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                            if current_subsection in subsection_indexes:
                                sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['content'] = subsection_content
                            else:
                                if current_subsection not in skip_tags and current_subsection != "On this page" and current_subsection != "On this page:":
                                    sections_with_content[section_index]['subsections'].append({
                                        'content': subsection_content
                                    })
                                    subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1
                        current_subsection = line['text']
                        next_is_subsection = (i + 1 < len(text_with_coords)
                            and text_with_coords[i + 1]['chars'][0]['fontname'].find("Lato-Bold")
                            and SUBSECTION_MIN_SIZE <= text_with_coords[i + 1]['chars'][0]['size'] < SUBSECTION_MAX_SIZE
                            )
                        if next_is_subsection:
                            subsection_title = text + " " + text_with_coords[i + 1]['text']
                            current_subsection = subsection_title
                            tracked_line = text_with_coords[i + 1]['text']
                        else:
                            if footers:
                                last_line = text_with_coords[-2]['text']
                                
                                if last_line and last_line == current_subsection:
                                    if page_num + 1 < len(pdf.pages):
                                        next_page = pdf.pages[page_num + 1]
                                        next_page_lines = next_page.extract_text_lines()
                                        if header:
                                            first_line = next_page_lines[1]
                                            if first_line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= first_line['chars'][0]['size'] < SUBSECTION_MAX_SIZE:
                                                subsection_title = text + " " + first_line['text']
                                                current_subsection = subsection_title
                                                tracked_line = first_line['text']
                        current_content = []
                    elif current_subsection != "On this page" or current_subsection != "On this page:":
                        current_content.append(line['text'])
                    
                        
                    if current_subsection and current_content:
                        subsection_content = current_subsection + ": " + clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                        if current_subsection in subsection_indexes:
                            sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['content'] = subsection_content
                        else:
                            if current_subsection not in skip_tags and current_subsection != "On this page" and current_subsection != "On this page:":  # Skip subsection if in skip_tags
                                sections_with_content[section_index]['subsections'].append({
                                    'content': subsection_content
                                })
                                subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1   
                    elif current_section and current_content:
                        sections_with_content[-1]['content'] = clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                        
                    
                    # handle no section
                    if not any(is_section) and current_content:
                        current_section = "Other Resources"
                        clean_content_str = clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)

                        # Check if "Other Resources" already exists in sections_with_content
                        existing_section = next((section for section in sections_with_content if section['section'] == current_section), None)

                        if existing_section:
                            # Replace the existing "Other Resources" content
                            existing_section['content'] = clean_content_str
                        else:
                            # Append a new "Other Resources" section
                            sections_with_content.append({
                                'tags': [],
                                'section': current_section,
                                'subsections': [],
                                'content': clean_content_str,
                            })
            return sections_with_content
        
        else:
            is_section = [(line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= line['chars'][0]['size'] < SECTION_MAX_SIZE) for page in pdf.pages for line in page.extract_text_lines()]
            is_subsection = [(line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= line['chars'][0]['size'] < SUBSECTION_MAX_SIZE) for page in pdf.pages for line in page.extract_text_lines()]
            for page_num, page in enumerate(pdf.pages):
                bboxes = [table for table in page.find_tables()]
                if not bboxes:
                    for i, line in enumerate(page.extract_text_lines()):
                        text = line['text']
                        if text == tracked_line:
                            continue
                        if text not in skip_tags:
                            # Check if line is a section
                            if line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= line['chars'][0]['size'] < SECTION_MAX_SIZE:
                                if current_section and current_content:
                                    sections_with_content[-1]['content'] = ' '.join(current_content).strip()
                                if text.lower() not in skip_tags:
                                    current_section = text
                                    next_is_section = (i + 1 < len(page.extract_text_lines())
                                        and page.extract_text_lines()[i + 1]['chars'][0]['fontname'].find("Lato-Bold")
                                        and SECTION_MIN_SIZE <= page.extract_text_lines()[i + 1]['chars'][0]['size'] < SECTION_MAX_SIZE
                                    )
                                    if next_is_section:
                                        section_title = text + " " + page.extract_text_lines()[i + 1]['text']
                                        current_section = section_title
                                        tracked_line = page.extract_text_lines()[i + 1]['text']
                                    else:
                                        if footers:
                                            last_line = page.extract_text_lines()[-2]['text']
                                            
                                            if last_line and last_line == current_section:
                                                if page_num + 1 < len(pdf.pages):
                                                    next_page = pdf.pages[page_num + 1]
                                                    next_page_lines = next_page.extract_text_lines()
                                                    if header:
                                                        first_line = next_page_lines[1]
                                                        if first_line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= first_line['chars'][0]['size'] < SECTION_MAX_SIZE:
                                                            section_title = text + " " + first_line['text']
                                                            current_section = section_title
                                                            tracked_line = first_line['text']
                                    current_content = []
                                    if category != None:
                                        sections_with_content.append({
                                            'tags': category,
                                            'section': current_section,
                                            'subsections': [],
                                            'table_content': [],
                                            'content': ''
                                        })
                                    else:
                                        sections_with_content.append({
                                            'tags': [],
                                            'section': current_section,
                                            'subsections': [],
                                            'table_content': [],
                                            'content': ''
                                        })
                                    section_index = len(sections_with_content) - 1
                                    subsection_indexes = {}
                            
                            # Check if line is a subsection
                            elif line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= line['chars'][0]['size'] < SUBSECTION_MAX_SIZE:
                                if current_subsection and current_content:
                                    subsection_content = current_subsection + ": " + clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                                    if current_subsection in subsection_indexes:
                                        sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['content'] = subsection_content
                                    else:
                                        if current_subsection not in skip_tags and current_subsection != "On this page" and current_subsection != "On this page:":
                                            sections_with_content[section_index]['subsections'].append({
                                                'content': subsection_content
                                            })
                                            subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1
                                current_subsection = text
                                next_is_subsection = (i + 1 < len(page.extract_text_lines())
                                    and page.extract_text_lines()[i + 1]['chars'][0]['fontname'].find("Lato-Bold")
                                    and SUBSECTION_MIN_SIZE <= page.extract_text_lines()[i + 1]['chars'][0]['size'] < SUBSECTION_MAX_SIZE
                                    )
                                if next_is_subsection:
                                    subsection_title = text + " " + page.extract_text_lines()[i + 1]['text']
                                    current_subsection = subsection_title
                                    tracked_line = page.extract_text_lines()[i + 1]['text']
                                else:
                                    if footers:
                                        last_line = page.extract_text_lines()[-2]['text']
                                        
                                        if last_line and last_line == current_subsection:
                                            if page_num + 1 < len(pdf.pages):
                                                next_page = pdf.pages[page_num + 1]
                                                next_page_lines = next_page.extract_text_lines()
                                                if header:
                                                    first_line = next_page_lines[1]
                                                    if first_line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= first_line['chars'][0]['size'] < SUBSECTION_MAX_SIZE:
                                                        subsection_title = text + " " + first_line['text']
                                                        current_subsection = subsection_title
                                                        tracked_line = first_line['text']
                                current_content = []
                            elif current_subsection != "On this page" or current_subsection != "On this page:":
                                current_content.append(text)
                        if current_subsection and current_content:
                            subsection_content = current_subsection + ": " + clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                            if current_subsection in subsection_indexes:
                                sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['content'] = subsection_content
                            else:
                                if current_subsection not in skip_tags:
                                    sections_with_content[section_index]['subsections'].append({
                                        'content': subsection_content
                                    })
                                    subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1
                        elif current_section and current_content:
                            sections_with_content[-1]['content'] = clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                            
                    if not any(is_section) and current_content:
                        current_section = "Other Resources"
                        clean_content_str = clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)

                        # Check if "Other Resources" already exists in sections_with_content
                        existing_section = next((section for section in sections_with_content if section['section'] == current_section), None)

                        if existing_section:
                            # Replace the existing "Other Resources" content
                            existing_section['content'] = clean_content_str
                        else:
                            # Append a new "Other Resources" section
                            sections_with_content.append({
                                'tags': [],
                                'section': current_section,
                                'subsections': [],
                                'content': clean_content_str,
                            })
                else:
                    table_content = None
                    table_content_extracted = set()
                    bboxes = []
                    tables = page.find_tables()
                    for table in tables:
                        bboxes.append(table.bbox)
                    for line in page.extract_text_lines():
                        text = line['text']
                        if text == tracked_line:
                            continue
                        line_bbox = (line['x0'], line['top'], line['x1'], line['bottom'])
                            
                        # Make sure the line is not part of a table
                        if not any(
                            bbox[0] <= line_bbox[2] and bbox[2] >= line_bbox[0] and
                            bbox[1] <= line_bbox[3] and bbox[3] >= line_bbox[1]
                            for bbox in bboxes
                        ):
                            if text not in skip_tags:
                                if line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= line['chars'][0]['size'] < SECTION_MAX_SIZE:
                                    if current_section and current_content:
                                        sections_with_content[-1]['content'] = ' '.join(current_content).strip()
                                    if text.lower() not in skip_tags:
                                        current_section = text
                                        next_is_section = (i + 1 < len(page.extract_text_lines())
                                            and page.extract_text_lines()[i + 1]['chars'][0]['fontname'].find("Lato-Bold")
                                            and SECTION_MIN_SIZE <= page.extract_text_lines()[i + 1]['chars'][0]['size'] < SECTION_MAX_SIZE
                                            )
                                        if next_is_section:
                                            section_title = text + " " + page.extract_text_lines()[i + 1]['text']
                                            current_section = section_title
                                            tracked_line = page.extract_text_lines()[i + 1]['text']
                                        else:
                                            if footers:
                                                last_line = page.extract_text_lines()[-2]['text']
                                                
                                                if last_line and last_line == current_section:
                                                    if page_num + 1 < len(pdf.pages):
                                                        next_page = pdf.pages[page_num + 1]
                                                        next_page_lines = next_page.extract_text_lines()
                                                        if header:
                                                            first_line = next_page_lines[1]
                                                            if first_line['chars'][0]['fontname'].find("Lato-Bold") and SECTION_MIN_SIZE <= first_line['chars'][0]['size'] < SECTION_MAX_SIZE:
                                                                section_title = text + " " + first_line['text']
                                                                current_section = section_title
                                                                tracked_line = first_line['text']
                                        current_content = []
                                        if category != None:
                                            sections_with_content.append({
                                                'tags': category,
                                                'section': current_section,
                                                'subsections': [],
                                                'table_content': [],
                                                'content': ''
                                            })
                                        else:
                                            sections_with_content.append({
                                                'tags': [],
                                                'section': current_section,
                                                'subsections': [],
                                                'table_content': [],
                                                'content': ''
                                            })
                                        section_index = len(sections_with_content) - 1
                                        subsection_indexes = {}
                                elif line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= line['chars'][0]['size'] < SUBSECTION_MAX_SIZE:
                                    if current_subsection and current_content:
                                        subsection_content = current_subsection + ": " + clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                                        if current_subsection in subsection_indexes:
                                            sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['content'] = subsection_content
                                        else:
                                            if current_subsection not in skip_tags and current_subsection != "On this page" and current_subsection != "On this page:":
                                                sections_with_content[section_index]['subsections'].append({
                                                    'content': subsection_content
                                                })
                                                subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1
                                    current_subsection = text
                                    next_is_subsection = (i + 1 < len(page.extract_text_lines())
                                        and page.extract_text_lines()[i + 1]['chars'][0]['fontname'].find("Lato-Bold")
                                        and SUBSECTION_MIN_SIZE <= page.extract_text_lines()[i + 1]['chars'][0]['size'] < SUBSECTION_MAX_SIZE
                                        )
                                    if next_is_subsection:
                                        subsection_title = text + " " + page.extract_text_lines()[i + 1]['text']
                                        current_subsection = subsection_title
                                        tracked_line = page.extract_text_lines()[i + 1]['text']
                                    else:
                                        if footers:
                                            last_line = page.extract_text_lines()[-2]['text']
                                            
                                            if last_line and last_line == current_subsection:
                                                if page_num + 1 < len(pdf.pages):
                                                    next_page = pdf.pages[page_num + 1]
                                                    next_page_lines = next_page.extract_text_lines()
                                                    if header:
                                                        first_line = next_page_lines[1]
                                                        if first_line['chars'][0]['fontname'].find("Lato-Bold") and SUBSECTION_MIN_SIZE <= first_line['chars'][0]['size'] < SUBSECTION_MAX_SIZE:
                                                            subsection_title = text + " " + first_line['text']
                                                            current_subsection = subsection_title
                                                            tracked_line = first_line['text']
                                    current_content = []
                                elif current_subsection != "On this page" or current_subsection != "On this page:":
                                    current_content.append(text)
                            if current_subsection and current_content:
                                subsection_content = current_subsection + ": " + clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)
                                if current_subsection in subsection_indexes:
                                    sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['content'] = subsection_content
                                else:
                                    if current_subsection not in skip_tags:
                                        sections_with_content[section_index]['subsections'].append({
                                            'content': subsection_content
                                        })
                                        subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1
                            elif current_section and current_content:
                                sections_with_content[-1]['content'] = clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)

                        else:
                            # Check the line_bbox against the table bboxes then get the index of the table bbox
                            table_index = best_matching_table(line_bbox, bboxes)
                            if table_index not in table_content_extracted:
                                table_extraction = extract_table_content(pdf_path)
                                if table_extraction:
                                    if table_extraction not in sections_with_content[section_index]['table_content'] and not current_subsection:
                                        sections_with_content[section_index]['table_content'].append(table_extraction)
                                    elif table_extraction not in sections_with_content[section_index]['table_content']:
                                        sections_with_content[section_index]['table_content'].append(table_extraction)
                                    elif current_subsection:
                                        if current_subsection in subsection_indexes:
                                            if 'table_content' in sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]:
                                                sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['table_content'].append(table_extraction)
                                            else:
                                                sections_with_content[section_index]['subsections'][subsection_indexes[current_subsection]]['table_content'] = [table_extraction]
                                        else:
                                            sections_with_content[section_index]['subsections'].append({
                                                'table_content': [table_extraction]
                                            })
                                            subsection_indexes[current_subsection] = len(sections_with_content[section_index]['subsections']) - 1
                                    table_content_extracted.add(table_index)   
                                    
                    
                    if not any(is_section) and current_content:
                        current_section = "Other Resources"
                        clean_content_str = clean_content(' '.join(current_content).strip(), header=header, footers=footers, txt_removed=txt_removed)

                        # Check if "Other Resources" already exists in sections_with_content
                        existing_section = next((section for section in sections_with_content if section['section'] == current_section), None)

                        if existing_section:
                            # Replace the existing "Other Resources" content
                            existing_section['content'] = clean_content_str
                        else:
                            # Append a new "Other Resources" section
                            sections_with_content.append({
                                'tags': [],
                                'section': current_section,
                                'subsections': [],
                                'content': clean_content_str,
                            })
            return sections_with_content    
        
        
def split_subsections(sections):
    docs = []
    for section in sections:
        if section['subsections'] != []:
            for subsection in section['subsections']:
                if 'table_content' in subsection:
                    doc = {
                        'tags': section['tags'],
                        'section': section['section'],
                        'content': subsection['content'],
                        'table_content': subsection['table_content']
                    }
                    docs.append(doc)
                else:
                    doc = {
                        'tags': section['tags'],
                        'section': section['section'],
                        'content': subsection['content']
                    }
                    docs.append(doc)
        else:
            if 'table_content' in section:
                doc = {
                    'tags': section['tags'],
                    'section': section['section'],
                    'content': section['content'],
                    'table_content': section['table_content']
                }
                docs.append(doc)
            else:
                doc = {
                    'tags': section['tags'],
                    'section': section['section'],
                    'content': section['content']
                }
                docs.append(doc)
    return docs


def combine_tbl_content(docs, pdf_path):
    if check_tables(pdf_path):
        for doc in docs:
            if 'table_content' in doc:
                paragraphs = []
                for table in doc['table_content']:
                    doc['content'] += "\n\n"
                    for row in table:
                        paragraph = f"\n -".join([f"{key.strip()}: {value.strip()}" for key, value in row.items()])
                        paragraphs.append(paragraph)    
                            
                doc['content'] += "\n\n".join(paragraphs)
                del doc['table_content']
            else:
                docs = docs
        return docs                           
    else:
        return docs
    
    
def filter_hyperlinks(hyperlinks, doc):
    content = doc['content']
    filtered_hyperlinks = []
    

    # Filter hyperlinks based on content
    for hyperlink in hyperlinks:
        if hyperlink['text'].lower() in content.lower() and hyperlink['text'] != '':
            filtered_hyperlinks.append(hyperlink)
    
    # Combine text for hyperlinks with the same URI
    combined_hyperlinks = {}
    for hyperlink in filtered_hyperlinks:
        uri = hyperlink['uri']
        text = hyperlink['text']
        if uri in combined_hyperlinks:
            combined_hyperlinks[uri]['text'] += "\n" + text
        else:
            combined_hyperlinks[uri] = {
                "uri": uri,
                "text": text
            }

    # Apply cleaning after combining
    for uri, content in combined_hyperlinks.items():
        combined_hyperlinks[uri]['text'] = clean_content(content['text'], txt_removed=None)
        
    final_filtered_hyperlinks = []
    for uri, content in combined_hyperlinks.items():
        combine_uri_text = content['uri'] + ": " + content['text']
        final_filtered_hyperlinks.append(combine_uri_text)
        
    return final_filtered_hyperlinks


def finalize_document(hyperlinks, docs, ref_link):
    idx = 0
    for doc in docs:
        doc['id'] = idx
        doc['hyperlinks'] = filter_hyperlinks(hyperlinks, doc)
        doc['ref_link'] = ref_link
        if doc['section'] not in doc['tags']:
            doc['tags'].append(doc['section'])
        del doc['section']
        idx += 1
    return docs


def data_preprocessing(pdf_path, skip_tags=None, category=None, txt_removed=None):
    headers, footers, ref_link = detect_headers_and_footers(pdf_path)
    hyperlinks = extract_hyperlinks(pdf_path)
    sections = detect_section_with_content(pdf_path, skip_tags=skip_tags, category=category, header=headers, footers=footers, txt_removed=txt_removed)
    sections = split_subsections(sections)
    sections = combine_tbl_content(sections, pdf_path)
    docs = finalize_document(hyperlinks, sections, ref_link)
    return docs


#! This function will be used after app admin has reviewed the processed data
def convert_to_langchain_docformat(docs, ofc_doc_id):
    final_docs = []
    for doc in docs:
        final_doc = Document(
            page_content=doc['content'],
            metadata={
                'ofc_doc_id': ofc_doc_id,
                'tags': doc['tags'],
                'text': doc['content'],
                'hyperlinks': doc['hyperlinks'],
                'ref_link': doc['ref_link']
            }
        )
        final_docs.append(final_doc)
    return final_docs

def convert_faq_to_langchain_docformat(faq_docs):
    final_faq_docs = []
    for faq_doc in faq_docs:
        final_faq_doc = Document(
            page_content=faq_doc['question'],
            metadata={
                "tags": faq_doc['tags'],
                "faq_id": faq_doc['faq_id'],
                "question": faq_doc['question'],
                "answer": faq_doc['answer'],
                "hyperlinks": faq_doc['hyperlinks'],
            }
        )
        final_faq_docs.append(final_faq_doc)
    return final_faq_docs

def extract_keys_hyperlinks_pinecone(docs):
    reformatted_hyperlinks = []
    hyperlink_text = {}
    for doc in docs:
        for hyperlink in doc["metadata"]["hyperlinks"]:
            hyperlink_text["hyperlink"] = hyperlink.split(": ")[0]
            hyperlink_text["text"] = hyperlink.split(": ")[1]
            reformatted_hyperlinks.append(hyperlink_text)
    return reformatted_hyperlinks