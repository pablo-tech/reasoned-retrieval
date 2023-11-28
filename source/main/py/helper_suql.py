from domain_knowledge import DomainSchema
from helper_parser import SummaryTagger, DataTransformer
from domain_knowledge import GiftSuql

from collections import defaultdict


class SchemaCreator(DomainSchema):

    def __init__(self, domain_name, domain_datasets, 
                 picked_columns, primary_key, price_column, 
                 subdomain_name, subdomain_column,
                 db_instance, completion_llm, is_verbose):
        super().__init__(data_sets=domain_datasets,
                         subdomain_name=subdomain_name,
                         subdomain_column=subdomain_column,
                         completion_llm=completion_llm,
                         is_verbose=is_verbose)
        self.domain_name = domain_name.upper()
        self.domain_datasets = domain_datasets
        self.picked_columns = picked_columns
        self.primary_key = primary_key
        self.price_column = price_column
        self.db_instance = db_instance
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def create_table(self, table_name, column_names):
        self.drop_table(table_name)
        self.new_table(self.create_sql(table_name, column_names))

    def drop_table(self, table_name):
        try:
            self.db_execute(f"DROP TABLE IF EXISTS {table_name};")
        except Exception as e:
            print("DELETE_TABLE_ERROR="+str(table_name)+"\t"+str(e))
            pass

    def new_table(self, create_sql):
        try:
            self.db_execute(create_sql)
            if self.is_verbose:
                print(create_sql)
        except Exception as e:
            print("CREATION_ERROR=" + self.domain_name + " " + str(e) + "\n" + str(create_sql))
            pass

    def db_execute(self, query):
        return self.db_instance.db_cursor.execute(query)

    def create_sql(self, table_name, column_names):
        column_txt = ""
        i = 1
        for column in sorted(column_names):
            column_txt += self.column_declaration(column)
            if i!=len(column_names):
                column_txt += ","
            column_txt += "\n"
            i += 1
        return f"""
    CREATE TABLE {table_name} (
    {column_txt}
    ) ;
    """

    def column_declaration(self, column_name):
        if column_name == self.primary_key:
            return f"""{self.primary_key} TEXT PRIMARY KEY"""
        if column_name == self.price_column:
            return f"""{self.price_column} FLOAT NOT NULL"""
        if "is_" in column_name:
            return f"""{column_name} BOOLEAN NOT NULL"""
        return f"""{column_name} TEXT NOT NULL"""

    def non_primary(self, primary_key, column_names):
        return sorted([name for name in column_names if name!=primary_key]) 

    def get_domain_name(self):
        return self.domain_name


class DatasetLoader(SchemaCreator):

    def __init__(self, nick_name, domain_name, domain_datasets,
                 subdomain_name, subdomain_column,  
                 picked_columns, primary_key, price_column, 
                 db_instance, completion_llm, is_verbose=False):
        super().__init__(domain_name, domain_datasets, 
                 picked_columns, primary_key, price_column, 
                 subdomain_name, subdomain_column,
                 db_instance, completion_llm, is_verbose)
        self.nick_name = nick_name
        self.db_instance = db_instance
        self.subdomain_column = subdomain_column
        self.table_name = self.set_table_name()

    def set_table_name(self):
        subdomain_name = self.subdomain_name
        name = self.get_domain_name() + "_" + self.nick_name 
        if subdomain_name != "":
            subdomain_name = subdomain_name.upper()
            subdomain_name = subdomain_name.replace("-","_")
            subdomain_name = subdomain_name.replace(".","_")
            name += "_" + subdomain_name
        return name

    def load_items(self):
        columns, products = self.get_columns(), self.get_products()
        print("COLUMNS=>" + str(columns))
        products = self.domain_unique_products(products, self.subdomain_name)
        table_name = self.get_table_name()
        self.create_table(table_name, columns)  
        self.batch_load(columns, products, table_name)      
        return columns, products
    
    def batch_load(self, columns, products, 
                   table_name, n=25):
        max = len(products)
        fails = 0
        i, j = 0, n
        while i < max:
            if j > max:
                j = max
            batch = products[i:j]
            insert_sql = self.prepare_load(columns, batch, table_name)
            # print("INSERT_SQL=>"+str(insert_sql))
            try:
                self.execute_load(insert_sql)
            except Exception as e:
                print("LOAD_EXCEPTION="+str(table_name)+"\t"+str(e) )
                fails+=1
                pass
            i+=n
            j+=n
        print("FAILURE_COUNT="+str(fails))
    
    def domain_unique_products(self, products_in, subdomain_name):
        if subdomain_name != "":
            products_in = [p for p in products_in if p[self.subdomain_column]==subdomain_name]
        products_out = []
        unique = set()
        for product in products_in:
            if product[self.primary_key] not in unique:
               unique.add(product[self.primary_key])
               products_out.append(product) 
        return products_out

    def prepare_load(self, columns, products, table_name):
        # print("PRODUCTS=>" + str(products))
        rows = DataTransformer.product_strs(products, columns, self.primary_key)
        for chunk in rows.split("\n")[:1]:
            if chunk != "":
                print("ROW=>" + str(chunk))
        insert_sql = self.get_sql(table_name, rows)
        return insert_sql

    def execute_load(self, insert_sql):
        self.db_instance.get_db_cursor().execute(insert_sql)
        self.db_instance.get_db_connection().commit()
    
    def get_sql(self, table_name, table_rows):
        return f"""
INSERT INTO {table_name} VALUES {table_rows}
"""    

    def get_schema_sql(self):
        return self.create_sql(self.get_table_name(), 
                               self.get_columns())
        
    def get_enums(self):
        return sorted(list(self.get_enum_values().keys()))
 
    def get_enum_values(self):
        return self.enum_values

    def get_table_name(self):
        return self.table_name

    def default_columns(self):
        columns = [self.primary_key,  self.price_column] 
        columns += self.summarize_columns
        return columns
    
    def set_columns(self):
        columns = self.default_columns()
        columns += list(self.get_enum_values().keys())
        columns = sorted(list(set(columns)))    
        return columns     

    def lower_enums(self):
        products_out = []
        for product_in in self.get_products():
            for k, v in product_in.items():
                if k in self.get_enum_values():
                    if not isinstance(v, bool):
                        v = v.lower()
                    product_in[k] = v
            products_out.append(product_in)       
        return products_out

    def get_columns(self):
        return self.columns
        
    def get_products(self):
        return self.products
    
    def get_enum_values(self):
        return self.enum_values


class DatasetReducer(DatasetLoader):

    def __init__(self, nick_name, domain_name, subdomain_dataset_func, 
                 subdomain_column, 
                 picked_columns, primary_key, price_column, summarize_columns,
                 db_instance, completion_llm, is_verbose=False):
        super().__init__(nick_name, domain_name, subdomain_dataset_func([]), 
                         "", subdomain_column, 
                         picked_columns, primary_key, price_column, 
                         db_instance, completion_llm, is_verbose)
        self.summarize_columns = summarize_columns
        self.products = self.get_domain_products()
        self.enum_values = self.set_enum_values()
        self.columns = self.set_columns()
        self.products = self.lower_enums()

    def set_enum_values(self):
        column_basis = self.get_domain_columns()
        exclude = [c for c in column_basis
                   if c not in self.picked_columns]
        exclude += self.default_columns()
        return DataTransformer.set_enum_values(column_basis,
                                               self.get_products(),
                                               exclude)        


class ContextParser(DatasetReducer):

    def __init__(self, domain_name, subdomain_dataset_func, 
                 subdomain_column,
                 picked_columns, primary_key, price_column, summarize_columns, 
                 db_instance, completion_llm, is_verbose=False):
        super().__init__("CONTEXT", domain_name, subdomain_dataset_func, 
                         subdomain_column,
                         picked_columns, primary_key, price_column, summarize_columns,
                         db_instance, completion_llm, is_verbose)

    def get_invocations(self):
        return [(self.domain_name,
                 self.get_columns(),
                 self.get_schema_sql(), 
                 self.get_enum_values(), 
                 self.get_fewshot_examples())]

    def get_fewshot_examples(self):
        columns = ", ".join(self.get_columns())
        table_name = self.get_table_name()
        return f"""        
Question: what Anna Sui products do you have? 
Answer: SELECT {columns} FROM {table_name} WHERE brand = 'anna sui';
Question: what GESTS products do you have?
Answer: SELECT {columns} FROM {table_name} WHERE brand = 'guess';
Question: what are the cheapest Scharf products?
Answer: SELECT {columns} FROM {table_name} WHERE brand = 'scharf' ORDER BY price ASC;
Question: "what are the cheapest Carpisa watches?"
Answer: SELECT {columns} FROM {table_name} WHERE brand = 'carpisa' AND title LIKE '%watch%' ORDER BY price ASC;
Question: "What is GW0403L2?"
Answer: SELECT {columns} FROM {table_name} WHERE title LIKE '%GW0403L2%';
Question: "Bags for men?"
Answer: SELECT {columns} FROM {table_name} WHERE title LIKE '%bag%' AND title NOT LIKE '%women%';
Question: "Glassses for women?"
Answer: SELECT {columns} FROM {table_name} WHERE title LIKE '%glass%' AND title NOT LIKE '% men%';
"""
    

class InferenceLoader(DatasetLoader):

    def __init__(self, is_run_inference, domain_name, subdomain_dataset_func,
                 subdomain_name, subdomain_column, 
                 picked_columns, primary_key, price_column,  
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose):
        super().__init__("INFERENCE", domain_name, subdomain_dataset_func([subdomain_name]), 
                         subdomain_name, subdomain_column, 
                         picked_columns, primary_key, price_column, 
                         db_instance, completion_llm, is_verbose)
        self.is_run_inference = is_run_inference
        self.subdomain_name = subdomain_name
        self.column_annotation = column_annotation
        self.primary_key = primary_key
        self.summarize_columns = summarize_columns
        self.summary_tagger = SummaryTagger(summarize_columns, primary_key,
                                            completion_llm, is_verbose)
        self.product_cache = GiftSuql()
        self.annotation_name = "is_"

    def augmented_products(self, n): 
        products = self.get_domain_products()
        products = self.summary_products(products)
        products = self.annotate_products(products)
        if n is not None:
            products = products[:n]
        return products
        
    def summary_products(self, context_products): 
        inference_products = []
        domain_products = self.product_by_domain(context_products)
        if not self.is_run_inference:
            for subdomain_name in domain_products.keys():
                products = self.product_cache.get_corpus(subdomain_name)
                inference_products.extend(products)
        else:
            for subdomain_name, context_products in domain_products.items():
                products = self.summary_tagger.invoke(context_products)
                inference_products.extend(products)
                self.product_cache.save_corpus(subdomain_name, products)
        inference_products = [DataTransformer.legal_product(p) for p in inference_products]                
        return inference_products
    
    def product_by_domain(self, products):
        domain_products = defaultdict(list)
        for product in products:
            domain_products[product[self.subdomain_column]].append(product)
        return domain_products
        
    def annotate_products(self, products):
        groupings = self.column_annotation.values()
        for grouping in groupings:
            for concept, values in grouping.items():
                concept = self.annotation_name + concept
                for value in values:
                    for product in products:
                        if value in product[self.subdomain_column]:
                            product[concept] = True
                        else:
                            product[concept] = False
        return products


class InferenceDomain(InferenceLoader):
    
    def __init__(self, is_run_inference, domain_name, subdomain_dataset_func,
                 subdomain_name, subdomain_column, 
                 picked_columns, primary_key, price_column, summarize_columns,
                 column_annotation, db_instance, 
                 completion_llm, is_verbose,
                 n=100):
        super().__init__(is_run_inference, domain_name, subdomain_dataset_func,
                         subdomain_name, subdomain_column,
                         picked_columns, primary_key, price_column,  
                         summarize_columns, column_annotation, 
                         db_instance, completion_llm, is_verbose)
        self.n = n    
        self.products = self.augmented_products(self.n)  
        self.column_basis = self.set_column_basis()  
        self.enum_values = self.set_enum_values()
        self.columns = self.set_columns()
        self.products = self.lower_enums()

    def set_enum_values(self):
        column_basis = self.get_column_basis()
        exclude = self.get_domain_columns()
        # column_basis = self.get_domain_columns()
        # exclude = [c for c in column_basis
        #            if c not in self.picked_columns]
        exclude += self.default_columns()
        return DataTransformer.set_enum_values(column_basis,
                                               self.get_products(),
                                               exclude)        

    def set_column_basis(self):
        columns = set()
        for p in self.get_products():
            columns.update(list(p.keys()))
        return columns
            
    def get_column_basis(self):
        return self.column_basis


class InferenceParser():

    def __init__(self, is_run_inference, domain_name, subdomain_dataset_func, 
                 subdomain_names, subdomain_column,
                 picked_columns, primary_key, price_column,  
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose=False): 
        self.domain_inference = {}
        for subdomain_name in subdomain_names:
            domain_inference = InferenceDomain(is_run_inference, domain_name, subdomain_dataset_func, 
                                               subdomain_name, subdomain_column,
                                               picked_columns, primary_key, price_column,  
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose)
            self.domain_inference[subdomain_name] = domain_inference

    def get_columns(self, subdomain_name):
        return self.domain_inference[subdomain_name].get_columns()

    def get_products(self, subdomain_name):
        return self.domain_inference[subdomain_name].get_products()

    def load_items(self):
        for subdomain_name, inference_domain in self.domain_inference.items():
            try:
                print("loading... " + str(subdomain_name))
                inference_domain.load_items()
            except Exception as e:
                print("LOAD_SUBDOMAIN_ERROR=" + str(subdomain_name))
                pass

    def get_invocations(self):
        return [(subdomain_name,
                 self.get_columns(subdomain_name), 
                 self.get_schema_sql(subdomain_name), 
                 self.get_enum_values(subdomain_name), 
                 self.get_fewshot_examples(subdomain_name)) 
                 for subdomain_name in self.domain_inference.keys()]

    def get_schema_sql(self, subdomain_name):
        return self.domain_inference[subdomain_name].get_schema_sql()

    def get_enum_values(self, subdomain_name):
        return self.domain_inference[subdomain_name].get_enum_values()            

    def get_fewshot_examples(self, subdomain_name):
        domain_inference = self.domain_inference[subdomain_name]
        columns = domain_inference.get_columns()
        columns = ", ".join(columns)
        table_name = domain_inference.get_table_name()
        return f"""        
Question: Antonio banderas Backpack? 
Answer: SELECT {columns} FROM {table_name} WHERE brand = 'antonio banderas';
Question: what 22 litter backpacks do you have?
Answer: SELECT {columns} FROM {table_name} WHERE product_size = '22 ltrs';
Question: what 2 wheel trolleys do your products have?
Answer: SELECT {columns} FROM {table_name} WHERE product_wheel_type = '2 wheel';
"""
# Question: what types of backpacks do you have? 
# Answer: SELECT {columns} FROM {table_name} WHERE product_type = 'backpack';


class WholisticParser():

    def __init__(self, context_parser, inference_parser):
        self.context_parser = context_parser
        self.inference_parser = inference_parser

    def schema_sql(self):
        return f"""
{self.context_parser.schema_sql()}

{self.inference_parser.schema_sql()}
"""
    def get_table_name(self):
        return f"""
{self.context_parser.get_table_name()} AS context JOIN
{self.inference_parser.get_table_name()} AS inference 
ON context.id = inference.id
""".replace("\n", " ")        

    def get_enum_values(self):
        return self.inference_parser.get_enum_values()
        # return { **self.context_parser.get_enum_values(), 
        #          **self.inference_parser.get_enum_values() }

    def get_fewshot_examples(self):
        columns = self.get_columns()
        columns = ", ".join(columns)
        return f"""        
Question: what backpacks do you have? 
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE inference.product_type = 'backpack';
Question: what 22 liter backpacks do you have?
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE inference.product_size = '22 Ltrs';
"""
# Question: what color trolleys do your products have?
# Answer: SELECT DISTINCT product_color FROM {self.get_table_name()} WHERE inference.product_type = 'duffle trolley bag';

    def get_columns(self):
        columns = ["context.id", "context.price", "context.title"] 
        columns += ["inference."+col for col in self.inference_parser.get_enums()]
        return columns    

    def get_invocations(self):
        return [(self.domain_name,
                 self.get_columns(),
                 self.get_schema_sql(), 
                 self.get_enum_values(), 
                 self.get_fewshot_examples())]
