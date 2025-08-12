"""
향상된 RAG 시스템 모듈
"""

from typing import List, Dict, Tuple
from langchain import hub
from langchain.chains import RetrievalQA
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from .config import Config


class EnhancedRAGSystem:
    """향상된 RAG 시스템 클래스"""
    
    def __init__(self, database, llm, use_query_optimization: bool = True, use_few_shot: bool = True):
        self.database = database
        self.llm = llm
        self.use_query_optimization = use_query_optimization
        self.use_few_shot = use_few_shot
        
        # RAG 체인 생성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm, 
            retriever=database.as_retriever(),
            chain_type_kwargs={"prompt": hub.pull("rlm/rag-prompt")}
        )
        
        # 쿼리 개선 체인 생성 (선택적)
        if self.use_query_optimization:
            self.query_improvement_chain = self._create_query_improvement_chain()
        
        # Few-Shot 체인 생성 (선택적)
        if self.use_few_shot:
            self.few_shot_chain = self._create_few_shot_chain()
        
        # 통합 체인 생성
        self.integrated_chain = self._create_integrated_chain()
    
    def _create_query_improvement_chain(self):
        """쿼리 개선을 위한 LCEL 체인 생성"""
        prompt = ChatPromptTemplate.from_template(f"""
            사용자의 질문을 보고, 우리의 세금 관련 사전을 참고해서 사용자의 질문을 변경해주세요.
            만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.
            그런 경우에는 질문만 리턴해주세요.
            
            세금 관련 사전: {Config.TAX_DICTIONARY}
            
            질문: {{question}}
            
            개선된 질문:
        """)
        
        return prompt | self.llm | StrOutputParser()
    
    def _create_few_shot_chain(self):
        """Few-Shot 예시를 사용한 고품질 답변 생성 체인"""
        print("\n🔧 Few-Shot 체인 생성 중...")
        print("=" * 50)
        
        # Few-Shot 예시 생성
        examples = []
        print(f"📚 답변 예시 {len(Config.ANSWER_EXAMPLES)}개 로드 중...")
        for i, example in enumerate(Config.ANSWER_EXAMPLES, 1):
            examples.append({
                "input": example["question"],
                "output": example["answer"]
            })
            print(f"   예시 {i}: {example['question'][:50]}...")
        
        # Few-Shot 프롬프트 템플릿
        print("\n📝 Few-Shot 프롬프트 템플릿 구성 중...")
        example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{input}"),
            ("ai", "{output}")
        ])
        print("   ✅ 예시 프롬프트 템플릿 생성 완료")
        
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            input_variables=["context", "question"]
        )
        print("   ✅ Few-Shot 프롬프트 템플릿 생성 완료")
        
        # 최종 프롬프트
        print("\n🎯 최종 프롬프트 구성 중...")
        final_prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 세금 전문가입니다. 다음 예시들을 참고하여 일관성 있고 정확한 답변을 제공하세요. 답변은 단계별로 명확하게 설명하고, 가능하면 구체적인 예시를 포함하세요."),
            few_shot_prompt,
            ("human", "문맥: {context}\n\n질문: {question}\n\n답변:")
        ])
        print("   ✅ 최종 프롬프트 생성 완료")
        
        print("🔗 Few-Shot 체인 구성 완료!")
        print("=" * 50)
        
        return final_prompt | self.llm | StrOutputParser()
    
    def _get_context(self, query):
        """검색된 문서를 컨텍스트로 변환"""
        print(f"\n🔍 컨텍스트 생성 시작 - 입력 타입: {type(query)}")
        try:
            # 입력 타입 처리
            if isinstance(query, dict):
                # dict에서 question 키 추출
                print(f"   📋 Dict 입력 감지: {list(query.keys())}")
                if 'question' in query:
                    actual_query = query['question']
                    print(f"   ✅ 'question' 키에서 쿼리 추출: '{actual_query}'")
                elif 'query' in query:
                    actual_query = query['query']
                    print(f"   ✅ 'query' 키에서 쿼리 추출: '{actual_query}'")
                else:
                    print(f"⚠️ dict에 question/query 키가 없음: {query.keys()}")
                    return "쿼리를 찾을 수 없습니다."
            elif isinstance(query, str):
                actual_query = query
                print(f"   ✅ 문자열 입력: '{actual_query}'")
            else:
                print(f"⚠️ 지원하지 않는 쿼리 타입: {type(query)}")
                return f"지원하지 않는 쿼리 타입: {type(query)}"
            
            # 쿼리 검증
            if not actual_query or not str(actual_query).strip():
                print("   ⚠️ 빈 쿼리 감지")
                return "빈 쿼리입니다."
            
            print(f"🔍 컨텍스트 검색: '{actual_query}'")
            docs = self.search_documents(actual_query, top_k=3)
            
            if docs:
                print(f"   📄 검색된 문서 수: {len(docs)}")
                context_parts = []
                for i, doc_item in enumerate(docs, 1):
                    try:
                        print(f"   📖 문서 {i} 처리 중...")
                        # 다양한 데이터 타입 처리
                        if hasattr(doc_item, 'page_content'):
                            # Document 객체인 경우
                            content = doc_item.page_content
                            print(f"      ✅ Document 객체 - 내용 길이: {len(content)}")
                            context_parts.append(content)
                        elif isinstance(doc_item, tuple) and len(doc_item) >= 1:
                            # (Document, score) 튜플인 경우
                            doc = doc_item[0]
                            score = doc_item[1] if len(doc_item) > 1 else "N/A"
                            print(f"      📊 튜플 형식 - 점수: {score}")
                            if hasattr(doc, 'page_content'):
                                content = doc.page_content
                                print(f"         ✅ Document 객체 - 내용 길이: {len(content)}")
                                context_parts.append(content)
                            elif isinstance(doc, str):
                                print(f"         ✅ 문자열 - 내용 길이: {len(doc)}")
                                context_parts.append(doc)
                        elif isinstance(doc_item, str):
                            # 문자열인 경우
                            print(f"      ✅ 문자열 - 내용 길이: {len(doc_item)}")
                            context_parts.append(doc_item)
                        elif isinstance(doc_item, dict):
                            # 딕셔너리인 경우
                            print(f"      📋 딕셔너리 형식 - 키: {list(doc_item.keys())}")
                            if 'page_content' in doc_item:
                                content = doc_item['page_content']
                                print(f"         ✅ 'page_content' 키 - 내용 길이: {len(content)}")
                                context_parts.append(content)
                            elif 'content' in doc_item:
                                content = doc_item['content']
                                print(f"         ✅ 'content' 키 - 내용 길이: {len(content)}")
                                context_parts.append(content)
                    except Exception as doc_error:
                        print(f"      ⚠️ 개별 문서 처리 중 오류: {doc_error}")
                        continue
                
                if context_parts:
                    context = "\n\n".join(context_parts)
                    total_length = len(context)
                    print(f"   ✅ 컨텍스트 생성 완료: {len(context_parts)}개 문서, 총 길이: {total_length}자")
                    print(f"   📝 컨텍스트 미리보기: {context[:100]}...")
                    return context
                else:
                    print("   ⚠️ 문서 내용을 추출할 수 없음")
                    return "문서 내용을 추출할 수 없습니다."
            else:
                print("   ⚠️ 검색 결과 없음")
                return "관련 문서를 찾을 수 없습니다."
        except Exception as e:
            print(f"⚠️ 컨텍스트 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return "문서 검색 중 오류가 발생했습니다."
    
    def _create_integrated_chain(self):
        """쿼리 개선, Few-Shot 학습, RAG를 통합한 LCEL 체인 생성"""
        # 안전한 체인 존재 여부 확인
        has_query_chain = hasattr(self, 'query_improvement_chain') and self.query_improvement_chain is not None
        has_few_shot_chain = hasattr(self, 'few_shot_chain') and self.few_shot_chain is not None
        
        if self.use_query_optimization and self.use_few_shot:
            # 쿼리 개선 + Few-Shot + RAG
            if has_query_chain and has_few_shot_chain:
                print("🔗 체인 구성: 쿼리 개선 + Few-Shot + RAG")
                chain = (
                    {"question": self.query_improvement_chain} 
                    | {"context": self._get_context, "question": lambda x: x.get("question", str(x))} 
                    | self.few_shot_chain
                )
            elif has_few_shot_chain:
                # 쿼리 개선 체인이 없으면 Few-Shot + RAG만
                print("🔗 체인 구성: Few-Shot + RAG (쿼리 개선 없음)")
                chain = (
                    {"context": lambda x: self._get_context(x), "question": lambda x: x.get("question", str(x))} 
                    | self.few_shot_chain
                )
            else:
                # Few-Shot 체인도 없으면 기본 RAG
                print("🔗 체인 구성: 기본 RAG")
                chain = self.qa_chain
        elif self.use_query_optimization:
            # 쿼리 개선 + 기본 RAG
            if has_query_chain:
                print("🔗 체인 구성: 쿼리 개선 + 기본 RAG")
                chain = {"query": self.query_improvement_chain} | self.qa_chain
            else:
                print("🔗 체인 구성: 기본 RAG")
                chain = self.qa_chain
        elif self.use_few_shot:
            # Few-Shot + RAG (쿼리 개선 없음)
            if has_few_shot_chain:
                print("🔗 체인 구성: Few-Shot + RAG")
                chain = (
                    {"context": lambda x: self._get_context(x), "question": lambda x: x.get("question", str(x))} 
                    | self.few_shot_chain
                )
            else:
                print("🔗 체인 구성: 기본 RAG")
                chain = self.qa_chain
        else:
            # 기본 RAG만
            print("🔗 체인 구성: 기본 RAG")
            chain = self.qa_chain
        
        return chain
    
    def improve_query(self, query: str) -> str:
        """LLM을 통해 쿼리 개선"""
        if not self.use_query_optimization or not hasattr(self, 'query_improvement_chain') or self.query_improvement_chain is None:
            return query
        
        try:
            improved_query = self.query_improvement_chain.invoke({"question": query})
            return improved_query.strip()
        except Exception as e:
            print(f"⚠️  쿼리 개선 중 오류: {e}")
            return query
    
    def search_documents(self, query: str, top_k: int = Config.TOP_K_DOCUMENTS) -> List[Tuple]:
        """문서 검색 수행"""
        try:
            if not query or not isinstance(query, str):
                print(f"⚠️ 잘못된 쿼리 타입: {type(query)}")
                return []
            
            # 쿼리 정리
            clean_query = str(query).strip()
            if not clean_query:
                print("⚠️ 빈 쿼리")
                return []
            
            results = self.database.similarity_search_with_score(clean_query, k=top_k)
            
            # 결과 검증
            if not results:
                print("⚠️ 검색 결과가 없습니다.")
                return []
            
            # 결과 타입 검증 및 정리
            validated_results = []
            for i, result in enumerate(results):
                try:
                    if isinstance(result, tuple) and len(result) >= 2:
                        doc, score = result[0], result[1]
                        validated_results.append((doc, score))
                    elif hasattr(result, 'page_content'):
                        # Document 객체만 있는 경우
                        validated_results.append((result, 1.0))
                    else:
                        print(f"⚠️ 잘못된 결과 형식 (인덱스 {i}): {type(result)}")
                except Exception as item_error:
                    print(f"⚠️ 결과 항목 처리 중 오류 (인덱스 {i}): {item_error}")
                    continue
            
            print(f"✅ 검색 완료: {len(validated_results)}개 문서")
            return validated_results
            
        except Exception as e:
            print(f"⚠️ 검색 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_query_with_improvement(self, query: str) -> Dict:
        """쿼리 개선 후 RAG 처리"""
        print("\n🔧 쿼리 처리:")
        print("=" * 60)
        
        # 1. 쿼리 개선 (선택적)
        print(f"1️⃣ 원본 쿼리: '{query}'")
        if self.use_query_optimization:
            improved_query = self.improve_query(query)
            print(f"2️⃣ 개선된 쿼리: '{improved_query}'")
            search_query = improved_query
        else:
            print("2️⃣ 쿼리 최적화 비활성화 - 원본 쿼리 사용")
            improved_query = query
            search_query = query
        print("-" * 40)
        
        # 2. 쿼리로 문서 검색
        print("3️⃣ 문서 검색 수행 중...")
        retrieved_docs_with_scores = self.search_documents(search_query)
        retrieved_docs = [doc for doc, _ in retrieved_docs_with_scores]
        print(f"   검색된 문서 수: {len(retrieved_docs)}")
        print("-" * 40)
        
        # 3. AI 응답 생성
        print("4️⃣ AI 응답 생성 중...")
        import time
        import threading
        import queue
        
        def run_with_timeout(func, args, timeout=30):
            """타임아웃과 함께 함수 실행 (Streamlit 호환)"""
            import concurrent.futures
            
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args)
                    result = future.result(timeout=timeout)
                    return result
            except concurrent.futures.TimeoutError:
                return None  # 타임아웃
            except Exception as e:
                raise e
        
        try:
            # Few-Shot 체인 사용 여부에 따른 처리
            if self.use_few_shot and hasattr(self, 'few_shot_chain'):
                print("   Few-Shot 체인 사용 중...")
                print("   🔄 Few-Shot 체인 실행 시작...")
                
                if self.use_query_optimization:
                    # 쿼리 개선 + Few-Shot + RAG
                    print("   📝 쿼리 개선 + Few-Shot + RAG 체인 실행...")
                    print("   🔗 체인 구성:")
                    print("      1. 쿼리 개선 체인 → question")
                    print("      2. 컨텍스트 생성 + question 추출")
                    print("      3. Few-Shot 체인 → 최종 답변")
                    
                    ai_response = run_with_timeout(
                        self.integrated_chain.invoke, 
                        [{"question": query}], 
                        30
                    )
                else:
                    # Few-Shot + RAG (쿼리 개선 없음)
                    print("   📝 Few-Shot + RAG 체인 실행 (쿼리 개선 없음)...")
                    print("   🔗 체인 구성:")
                    print("      1. 컨텍스트 생성 + question 추출")
                    print("      2. Few-Shot 체인 → 최종 답변")
                    
                    ai_response = run_with_timeout(
                        self.integrated_chain.invoke, 
                        [{"question": query}], 
                        30
                    )
                
                if ai_response is None:
                    raise TimeoutError("AI 응답 생성 시간 초과")
                
                print(f"   ✅ Few-Shot 체인 실행 완료!")
                print(f"   📊 응답 타입: {type(ai_response)}")
                
                # Few-Shot 체인의 경우 직접 문자열 반환
                if isinstance(ai_response, str):
                    response_text = ai_response
                    print(f"   📝 문자열 응답 - 길이: {len(response_text)}")
                else:
                    response_text = ai_response.get('result', str(ai_response))
                    print(f"   📝 딕셔너리 응답 - 키: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'N/A'}")
                
                print(f"   🎯 최종 응답 길이: {len(response_text)}")
                    
            else:
                print("   기본 QA 체인 사용 중...")
                result = run_with_timeout(
                    self.qa_chain, 
                    [{"query": search_query}], 
                    30
                )
                if result is None:
                    raise TimeoutError("AI 응답 생성 시간 초과")
                response_text = result['result']
            
        except TimeoutError:
            print("⚠️  AI 응답 생성 시간 초과 (30초)")
            response_text = "죄송합니다. 응답 생성에 시간이 오래 걸리고 있습니다. 다시 시도해주세요."
        except Exception as e:
            print(f"⚠️  AI 응답 생성 중 오류: {e}")
            try:
                # 폴백: 기본 QA 체인으로 재시도
                print("   폴백 체인으로 재시도 중...")
                result = run_with_timeout(
                    self.qa_chain, 
                    [{"query": search_query}], 
                    15
                )
                if result is None:
                    raise TimeoutError("폴백 체인도 시간 초과")
                response_text = result['result']
            except Exception as fallback_error:
                print(f"⚠️  폴백 체인도 실패: {fallback_error}")
                response_text = f"죄송합니다. AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
        
        print("=" * 60)
        
        return {
            'success': True,
            'answer': response_text,
            'original_query': query,
            'improved_query': improved_query,
            'retrieved_docs': retrieved_docs,
            'retrieved_docs_with_scores': retrieved_docs_with_scores,
            'optimization_used': self.use_query_optimization,
            'few_shot_used': self.use_few_shot
        }
    
    def toggle_query_optimization(self):
        """쿼리 최적화 기능 토글"""
        self.use_query_optimization = not self.use_query_optimization
        
        if self.use_query_optimization and not self.query_improvement_chain:
            self.query_improvement_chain = self._create_query_improvement_chain()
            print("✅ 쿼리 최적화 기능이 활성화되었습니다.")
        elif not self.use_query_optimization:
            self.query_improvement_chain = None
            print("🚫 쿼리 최적화 기능이 비활성화되었습니다.")
        
        # 통합 체인 재생성
        self.integrated_chain = self._create_integrated_chain()
    
    def toggle_few_shot(self):
        """Few-Shot 학습 기능 토글"""
        self.use_few_shot = not self.use_few_shot
        
        if self.use_few_shot and not hasattr(self, 'few_shot_chain'):
            self.few_shot_chain = self._create_few_shot_chain()
            print("✅ Few-Shot 학습 기능이 활성화되었습니다.")
        elif not self.use_few_shot:
            self.few_shot_chain = None
            print("🚫 Few-Shot 학습 기능이 비활성화되었습니다.")
        
        # 통합 체인 재생성
        self.integrated_chain = self._create_integrated_chain()
    
    def get_optimization_status(self) -> Dict:
        """쿼리 최적화 상태 정보 반환"""
        return {
            'query_optimization_enabled': self.use_query_optimization,
            'few_shot_enabled': self.use_few_shot,
            'has_query_chain': hasattr(self, 'query_improvement_chain') and self.query_improvement_chain is not None,
            'has_few_shot_chain': hasattr(self, 'few_shot_chain') and self.few_shot_chain is not None,
            'dictionary_count': len(Config.TAX_DICTIONARY),
            'example_count': len(Config.ANSWER_EXAMPLES),
            'current_chain_type': self._get_chain_type_description()
        }
    
    def _get_chain_type_description(self) -> str:
        """현재 사용 중인 체인 타입 설명 반환"""
        if self.use_query_optimization and self.use_few_shot:
            return "쿼리 개선 + Few-Shot + RAG"
        elif self.use_query_optimization:
            return "쿼리 개선 + 기본 RAG"
        elif self.use_few_shot:
            return "Few-Shot + RAG"
        else:
            return "기본 RAG" 